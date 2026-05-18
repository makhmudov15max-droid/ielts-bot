import os
import json
import gspread
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
import config

# Keyboards klaviaturalarini import qilamiz
from Keyboards.main_menu import (
    get_sheets_teachers_keyboard,
    get_sheets_teacher_options_keyboard,
    get_sheets_ielts_scores_keyboard
)

sheets_router = Router()

try:
    ADMIN_ID = int(config.ADMIN_ID)
except (ValueError, AttributeError):
    ADMIN_ID = 6500594896

# ==================== 📊 JONLI GOOGLE SHEETS ULASH TIZIMI ====================
sheet = None  # Global o'zgaruvchi

def connect_to_sheets():
    """Google Sheets'ga ulanish funksiyasi - har safar chaqirilganda qayta ulanadi"""
    global sheet
    try:
        railway_creds = os.getenv("GOOGLE_CREDS_JSON")
        
        if railway_creds:
            print("Railway: GOOGLE_CREDS_JSON topildi, ulanish boshlandi...")
            creds_dict = json.loads(railway_creds)
            client = gspread.service_account_from_dict(creds_dict)
        else:
            print("Railway: GOOGLE_CREDS_JSON topilmadi, lokal fayldan o'qilmoqda...")
            if not os.path.exists("google_creds.json"):
                print("❌ XATO: 'google_creds.json' fayli ham topilmadi!")
                return None
            client = gspread.service_account(filename="google_creds.json")
        
        spreadsheet = client.open_by_key("1X7NWhD18N4LgVv9w7XmUoZ6YIeS50nF57zP93YjEw_Q")
        ws = spreadsheet.worksheet("Ustozlar")
        print("✅ Google Sheets 'Ustozlar' sahifasiga ulanish muvaffaqiyatli!")
        return ws
        
    except json.JSONDecodeError as e:
        print(f"❌ GOOGLE_CREDS_JSON formati noto'g'ri (JSON xatolik): {e}")
        return None
    except gspread.exceptions.SpreadsheetNotFound:
        print("❌ Jadval topilmadi! Spreadsheet ID yoki ruxsatni tekshiring.")
        return None
    except gspread.exceptions.WorksheetNotFound:
        print("❌ 'Ustozlar' nomli sahifa topilmadi! Sahifa nomini tekshiring.")
        return None
    except Exception as e:
        print(f"❌ GOOGLE API ULANISHDA KUTILMAGAN XATOLIK: {type(e).__name__}: {e}")
        return None

# Bot ishga tushganda birinchi marta ulanishga harakat qilamiz
sheet = connect_to_sheets()
# ==============================================================================


def get_teachers_from_google_sheets():
    """Ustozlar ro'yxatini Google Sheets'dan o'qiydi"""
    global sheet
    
    # Agar sheet None bo'lsa, qayta ulanishga harakat qilamiz
    if not sheet:
        print("Sheet None, qayta ulanish urinilmoqda...")
        sheet = connect_to_sheets()
        
    if not sheet:
        print("❌ Sheet obyekti yaratilmagan, ma'lumot o'qib bo'lmadi!")
        return []
    
    try:
        all_records = sheet.get_all_values()
        print(f"Sheets'dan {len(all_records)} qator o'qildi")
        
        if len(all_records) <= 1:
            print("Jadvalda ma'lumot yo'q yoki faqat sarlavha bor")
            return []
        
        # Birinchi qator (sarlavha) ni o'tkazib, qolganlarini qaytaramiz
        teachers = all_records[1:]
        print(f"Ustozlar soni: {len(teachers)}")
        
        # Har bir qatorda kamida 3 ta ustun borligini tekshiramiz
        valid_teachers = []
        for i, t in enumerate(teachers):
            if len(t) >= 3 and t[0].strip() and t[1].strip():
                valid_teachers.append(t)
            else:
                print(f"Eslatma: {i+2}-qator to'liq emas, o'tkazildi: {t}")
        
        return valid_teachers
        
    except gspread.exceptions.APIError as e:
        print(f"❌ Google API xatolik (limit yoki ruxsat muammosi): {e}")
        sheet = None  # Qayta ulanish uchun None qilamiz
        return []
    except Exception as e:
        print(f"❌ Ma'lumotlarni o'qishda kutilmagan xatolik: {type(e).__name__}: {e}")
        return []


# ==================== HANDLER'LAR ====================

@sheets_router.message(F.text == "👨🏻‍🏫 Ustoz/Ball")
async def process_sheets_teachers_menu(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    await message.answer("🔄 Google Sheets jadvalidan o'qituvchilar ro'yxati yuklanmoqda. Iltimos, kuting...")

    teachers = get_teachers_from_google_sheets()
    
    if not teachers:
        # Muammoni aniqroq ko'rsatamiz
        global sheet
        if not sheet:
            error_msg = (
                "❌ <b>Google Sheets'ga ulanib bo'lmadi!</b>\n\n"
                "Quyidagilarni tekshiring:\n"
                "1️⃣ Railway'da <code>GOOGLE_CREDS_JSON</code> variable to'g'ri o'rnatilganmi?\n"
                "2️⃣ Service account emailiga jadval 'Editor' ruxsati berilganmi?\n"
                "3️⃣ Google Sheets API va Google Drive API yoqilganmi?\n\n"
                "📋 Railway loglarida xato xabarini tekshiring."
            )
        else:
            error_msg = (
                "⚠️ <b>Ulanish muvaffaqiyatli, lekin ma'lumot topilmadi!</b>\n\n"
                "Quyidagilarni tekshiring:\n"
                "1️⃣ Jadvalda <b>'Ustozlar'</b> nomli sahifa bormi?\n"
                "2️⃣ 2-qatordan boshlab ma'lumot kiritilganmi?\n"
                "3️⃣ 1-qator sarlavha (ID, Ism, IELTS Ball) bo'lishi kerak."
            )
        await message.answer(error_msg, parse_mode="HTML")
        return

    await message.answer(
        text="👨‍🏫 <b>Google Sheets'dagi Ustozlar va ularning IELTS ballari:</b>\n\n"
             "Ballarni jonli yangilash yoki tekshirish uchun ustoz ustiga bosing:",
        parse_mode="HTML",
        reply_markup=get_sheets_teachers_keyboard(teachers)
    )


@sheets_router.callback_query(F.data == "back_to_gs_teachers")
async def back_to_sheets_teachers_callback(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    teachers = get_teachers_from_google_sheets()
    
    if not teachers:
        await call.message.edit_text(
            text="❌ Ma'lumotlarni qayta yuklab bo'lmadi. Iltimos, qaytadan <b>👨🏻‍🏫 Ustoz/Ball</b> tugmasini bosing.",
            parse_mode="HTML"
        )
        await call.answer()
        return
    
    await call.message.edit_text(
        text="👨‍🏫 <b>Google Sheets'dagi Ustozlar va ularning IELTS ballari:</b>\n\n"
             "Ballarni jonli yangilash yoki tekshirish uchun ustoz ustiga bosing:",
        parse_mode="HTML",
        reply_markup=get_sheets_teachers_keyboard(teachers)
    )
    await call.answer()


@sheets_router.callback_query(F.data.startswith("gs_viewt_"))
async def view_sheets_teacher_profile_callback(call: types.CallbackQuery):
    # "gs_viewt_ID" formatidan ID ni ajratib olamiz
    # ID o'zida "_" belgisi bo'lishi mumkin deb ehtiyot bo'lamiz
    t_id = call.data[len("gs_viewt_"):]
    
    teachers = get_teachers_from_google_sheets()
    target_teacher = next((t for t in teachers if t[0].strip() == t_id.strip()), None)
    
    if not target_teacher:
        await call.answer(f"❌ Ustoz topilmadi! (ID: {t_id})", show_alert=True)
        return

    # Ustunlar mavjudligini tekshiramiz
    ism = target_teacher[1] if len(target_teacher) > 1 else "Noma'lum"
    ball = target_teacher[2] if len(target_teacher) > 2 else "Kiritilmagan"

    text = (
        f"👤 <b>Ustoz Ma'lumotlari (Google Sheets)</b>\n\n"
        f"🆔 <b>ID:</b> {target_teacher[0]}\n"
        f"📝 <b>Ism Familiya:</b> {ism}\n"
        f"🎯 <b>Joriy IELTS Bali:</b> <code>{ball}</code>\n\n"
        f"<i>Ma'lumotlar onlayn jadvalingiz orqali boshqariladi.</i>"
    )
    await call.message.edit_text(
        text=text,
        parse_mode="HTML",
        reply_markup=get_sheets_teacher_options_keyboard(target_teacher[0])
    )
    await call.answer()


@sheets_router.callback_query(F.data.startswith("gs_editscore_"))
async def edit_sheets_teacher_score_callback(call: types.CallbackQuery):
    t_id = call.data[len("gs_editscore_"):]
    teachers = get_teachers_from_google_sheets()
    target_teacher = next((t for t in teachers if t[0].strip() == t_id.strip()), None)

    if not target_teacher:
        await call.answer("❌ Ustoz topilmadi!", show_alert=True)
        return

    ism = target_teacher[1] if len(target_teacher) > 1 else "Noma'lum"

    await call.message.edit_text(
        text=f"✍️ <b>{ism}</b> uchun yangi shaxsiy IELTS balini tanlang:\n"
             f"<i>(Tanlangan ball Google Sheets jadvalingizda yangilanadi)</i>",
        parse_mode="HTML",
        reply_markup=get_sheets_ielts_scores_keyboard(t_id)
    )
    await call.answer()


@sheets_router.callback_query(F.data.startswith("gs_setscore_"))
async def set_sheets_teacher_score_done_callback(call: types.CallbackQuery):
    global sheet
    
    # Format: "gs_setscore_BALL_ID"
    # Ball "6.5", "7.0" kabi bo'lishi mumkin, shuning uchun oxirgi qismni ID deb olamiz
    raw = call.data[len("gs_setscore_"):]  # "6.5_T001" yoki "7.0_T001"
    
    # Oxirgi "_" dan keyingi qism ID, boshqa qism ball
    last_underscore = raw.rfind("_")
    if last_underscore == -1:
        await call.answer("❌ Noto'g'ri format!", show_alert=True)
        return
    
    new_score = raw[:last_underscore]
    t_id = raw[last_underscore + 1:]

    teachers = get_teachers_from_google_sheets()
    row_index = -1
    t_name = ""

    for idx, t in enumerate(teachers):
        if t[0].strip() == t_id.strip():
            row_index = idx + 2  # +1 sarlavha, +1 Python 0-indexdan
            t_name = t[1] if len(t) > 1 else "Noma'lum"
            break

    if row_index == -1:
        await call.answer("❌ Ustoz topilmadi!", show_alert=True)
        return

    if not sheet:
        sheet = connect_to_sheets()
    
    if not sheet:
        await call.answer("❌ Google Sheets'ga ulanib bo'lmadi!", show_alert=True)
        return

    try:
        sheet.update_cell(row_index, 3, new_score)
        await call.message.edit_text(
            text=f"✅ <b>Google Sheets muvaffaqiyatli yangilandi!</b>\n\n"
                 f"👨‍🏫 Ustoz: <b>{t_name}</b>\n"
                 f"🎯 Yangi shaxsiy ball: <b>{new_score}</b>",
            parse_mode="HTML",
            reply_markup=get_sheets_teacher_options_keyboard(t_id)
        )
    except Exception as e:
        print(f"❌ update_cell xatolik: {e}")
        await call.answer(f"❌ Yangilashda xatolik: {type(e).__name__}", show_alert=True)
    
    await call.answer()
