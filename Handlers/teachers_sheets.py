import gspread
from oauth2client.service_account import ServiceAccountCredentials
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
import config

# Keyboards klaviaturalarini import qilamiz
from Keyboards.main_menu import (
    get_sheets_teachers_keyboard,
    get_sheets_teacher_options_keyboard,
    get_sheets_ielts_scores_keyboard
)

# Alohida yangi router ochamiz
sheets_router = Router()

try:
    ADMIN_ID = int(config.ADMIN_ID)
except ValueError:
    ADMIN_ID = 6500594896

# ==================== 📊 JONLI GOOGLE SHEETS ULASH TIZIMI ====================
try:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("google_creds.json", scope)
    client = gspread.authorize(creds)
    # Onlayn Google Sheets jadvalingiz nomini aniq kiriting
    sheet = client.open("Google_Sheets_Jadval_Nomi").worksheet("Ustozlar")
    print("Google Sheets 'Ustozlar' sahifasiga ulanish muvaffaqiyatli!")
except Exception as e:
    print(f"Google Sheets ulanishda xatolik yuz berdi: {e}")
    sheet = None

def get_teachers_from_google_sheets():
    if not sheet: return []
    try:
        all_records = sheet.get_all_values()
        if len(all_records) <= 1: return []
        return all_records[1:] # Sarlavha satridan keyingi ma'lumotlar
    except Exception as e:
        print(f"Ma'lumotlarni o'qishda xatolik: {e}")
        return []
# ==============================================================================

@sheets_router.message(F.text == "👨🏻‍🏫 Ustoz/Ball")
async def process_sheets_teachers_menu(message: types.Message):
    if message.from_user.id != ADMIN_ID: return 
    
    await message.answer("🔄 Google Sheets jadvalidan o'qituvchilar ro'yxati yuklanmoqda. Iltimos, kuting...")
    
    teachers = get_teachers_from_google_sheets()
    if not teachers:
        await message.answer("❌ Google Sheets 'Ustozlar' sahifasidan ma'lumotlarni o'qib bo'lmadi yoki sahifa bo'sh.")
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
    await call.message.edit_text(
        text="👨‍🏫 <b>Google Sheets'dagi Ustozlar va ularning IELTS ballari:</b>\n\n"
             "Ballarni jonli yangilash yoki tekshirish uchun ustoz ustiga bosing:",
        parse_mode="HTML",
        reply_markup=get_sheets_teachers_keyboard(teachers)
    )
    await call.answer()

@sheets_router.callback_query(F.data.startswith("gs_viewt_"))
async def view_sheets_teacher_profile_callback(call: types.CallbackQuery):
    t_id = call.data.split("_")[2]
    teachers = get_teachers_from_google_sheets()
    
    target_teacher = next((t for t in teachers if t[0] == t_id), None)
    if not target_teacher:
        await call.answer("Ustoz jadvaldan topilmadi!", show_alert=True)
        return
        
    text = (
        f"👤 <b>Ustoz Ma'lumotlari (Google Sheets)</b>\n\n"
        f"🆔 <b>ID:</b> {target_teacher[0]}\n"
        f"📝 <b>Ism Familiya:</b> {target_teacher[1]}\n"
        f"🎯 <b>Joriy IELTS Bali:</b> <code>{target_teacher[2]}</code>\n\n"
        f"<i>Ma'lumotlar onlayn jadvalingiz orqali boshqariladi.</i>"
    )
    await call.message.edit_text(text=text, parse_mode="HTML", reply_markup=get_sheets_teacher_options_keyboard(t_id))
    await call.answer()

@start_router.callback_query(F.data.startswith("gs_editscore_"))
async def edit_sheets_teacher_score_callback(call: types.CallbackQuery):
    t_id = call.data.split("_")[2]
    teachers = get_teachers_from_google_sheets()
    target_teacher = next((t for t in teachers if t[0] == t_id), None)
    
    await call.message.edit_text(
        text=f"✍️ <b>{target_teacher[1]}</b> uchun yangi shaxsiy IELTS balini tanlang:\n"
             f"<i>(Tanlangan ball Google Sheets jadvalingizda yangilanadi)</i>",
        parse_mode="HTML",
        reply_markup=get_sheets_ielts_scores_keyboard(t_id)
    )
    await call.answer()

@sheets_router.callback_query(F.data.startswith("gs_setscore_"))
async def set_sheets_teacher_score_done_callback(call: types.CallbackQuery):
    data_parts = call.data.split("_")
    new_score = data_parts[2]
    t_id = data_parts[3]
    
    teachers = get_teachers_from_google_sheets()
    row_index = -1
    t_name = ""
    
    for idx, t in enumerate(teachers):
        if t[0] == t_id:
            row_index = idx + 2 # Sarlavhadan keyingi qator indeksi
            t_name = t[1]
            break
            
    if row_index != -1 and sheet:
        sheet.update_cell(row_index, 3, new_score)
        await call.message.edit_text(
            text=f"✅ <b>Google Sheets muvaffaqiyatli yangilandi!</b>\n\n"
                 f"👨‍🏫 Ustoz: <b>{t_name}</b>\n"
                 f"🎯 Yangi shaxsiy ball: <b>{new_score}</b>",
            parse_mode="HTML",
            reply_markup=get_sheets_teacher_options_keyboard(t_id)
        )
    else:
        await call.answer("Xatolik: Google Sheets yangilanishida muammo yuz berdi.", show_alert=True)
    await call.answer()
