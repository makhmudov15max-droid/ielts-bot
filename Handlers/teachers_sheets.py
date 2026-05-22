import os
import json
import gspread
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
import config

sheets_router = Router()

try:
    ADMIN_ID = int(config.ADMIN_ID)
except ValueError:
    ADMIN_ID = 6500594896


# ================= ADMIN ROLINI TEKSHIRUVCHI FUNKSIYA (JSON fayldan o'qiydi) =================

def is_admin(user_id: int) -> bool:
    """Foydalanuvchi Admin yoki Owner rolida ekanligini tekshiradi"""
    USERS_FILE = "users.json"
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                users = json.load(f)
                user_info = users.get(str(user_id))
                if user_info:
                    role = user_info.get("role")
                    return role in ["Admin", "Owner"]
    except Exception as e:
        print(f"is_admin() xatosi: {e}")
    return False


# ==================== SHEETS KEYBOARDS ====================

def get_sheets_teachers_keyboard(teachers):
    keyboard = []
    for t in teachers:
        if len(t) >= 2:
            keyboard.append([
                types.InlineKeyboardButton(
                    text=f"👨‍🏫 {t[1]}",
                    callback_data=f"gs_viewt_{t[0]}"
                )
            ])
    return types.InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_sheets_teacher_options_keyboard(t_id):
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="✏️ IELTS ballni o'zgartirish",
                    callback_data=f"gs_editscore_{t_id}"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text="🔙 Orqaga",
                    callback_data="back_to_gs_teachers"
                )
            ]
        ]
    )


def get_sheets_ielts_scores_keyboard(t_id):
    scores = ["5.0", "5.5", "6.0", "6.5", "7.0", "7.5", "8.0", "8.5", "9.0"]
    keyboard = []
    row = []

    for score in scores:
        row.append(
            types.InlineKeyboardButton(
                text=score,
                callback_data=f"gs_setscore_{score}_{t_id}"
            )
        )
        if len(row) == 3:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.append([
        types.InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_gs_teachers")
    ])

    return types.InlineKeyboardMarkup(inline_keyboard=keyboard)


# ==================== GOOGLE SHEETS ULASH ====================

try:
    creds_json = os.getenv("GOOGLE_CREDS")
    if not creds_json:
        raise Exception("GOOGLE_CREDS topilmadi!")

    creds = json.loads(creds_json)
    client = gspread.service_account_from_dict(creds)
    sheet = client.open("EduControl").worksheet("Ustozlar")

    print("✅ Google Sheets muvaffaqiyatli ulandi!")
    test_data = sheet.get_all_values()
    print(f"📊 Topilgan qatorlar soni: {len(test_data)}")

except Exception as e:
    print(f"❌ Google ulanish xatosi: {e}")
    sheet = None


def get_teachers_from_google_sheets():
    if not sheet:
        print("Xatolik: 'sheet' obyekti yaratilmagan!")
        return []

    try:
        all_records = sheet.get_all_values()
        if len(all_records) <= 1:
            return []
        return all_records[1:]
    except Exception as e:
        print(f"Ma'lumotlarni o'qishda xatolik: {e}")
        return []


@sheets_router.message(F.text == "👨🏻‍🏫 Ustoz/Ball")
async def process_sheets_teachers_menu(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⚠️ Bu buyruq faqat administrator va owner uchun!")
        return

    await message.answer("🔄 Google Sheets jadvalidan o'qituvchilar ro'yxati yuklanmoqda. Iltimos, kuting...")

    teachers = get_teachers_from_google_sheets()

    if not teachers:
        await message.answer(
            "❌ Google Sheets 'Ustozlar' sahifasidan ma'lumotlarni o'qib bo'lmadi yoki sahifa bo'sh.\n\n"
            "⚠️ Iltimos, jadvalni bot pochtasiga Editor qilib ruxsat berganingizni tekshiring!"
        )
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

    target_teacher = next((t for t in teachers if len(t) >= 3 and t[0] == t_id), None)

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

    await call.message.edit_text(
        text=text,
        parse_mode="HTML",
        reply_markup=get_sheets_teacher_options_keyboard(t_id)
    )
    await call.answer()


@sheets_router.callback_query(F.data.startswith("gs_editscore_"))
async def edit_sheets_teacher_score_callback(call: types.CallbackQuery):
    t_id = call.data.split("_")[2]
    teachers = get_teachers_from_google_sheets()

    target_teacher = next((t for t in teachers if len(t) >= 2 and t[0] == t_id), None)
    teacher_name = target_teacher[1] if target_teacher else "Ustoz"

    await call.message.edit_text(
        text=f"✍️ <b>{teacher_name}</b> uchun yangi shaxsiy IELTS balini tanlang:\n"
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
        if len(t) >= 2 and t[0] == t_id:
            row_index = idx + 2
            t_name = t[1]
            break

    if row_index != -1 and sheet:
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
            print(f"❌ Google Sheets yangilash xatosi: {e}")
            await call.answer("Xatolik: Google Sheets yangilanishida muammo yuz berdi.", show_alert=True)
    else:
        await call.answer("Xatolik: Google Sheets yangilanishida muammo yuz berdi.", show_alert=True)

    await call.answer()
