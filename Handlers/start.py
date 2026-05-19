import asyncio
from calculators.cashier_calc import calculate_cashier_salary
from Handlers.states import CashierSalaryStates
from datetime import datetime, timedelta, timezone
from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from calculators.admin_calc import calculate_admin_salary
import config  
from Keyboards.main_menu import (
    main_menu_keyboard,
    get_main_menu,
    task_type_keyboard, 
    days_keyboard, 
    frequency_keyboard, 
    get_inline_days_keyboard,
    get_admin_approval_keyboard,
    proof_type_keyboard,
    assign_role_keyboard,
    get_task_complete_keyboard,
    get_remove_tasks_keyboard
)
from Handlers.states import TaskStates

start_router = Router()

try:
    ADMIN_ID = int(config.ADMIN_ID)
except ValueError:
    ADMIN_ID = 6500594896  

# ================= USERS JSON TIZIMI =================

import json
import os

USERS_FILE = "users.json"


def load_users():
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)

    except Exception as e:
        print(f"Users yuklash xatosi: {e}")

    return {
        str(ADMIN_ID): {
            "role": "Owner",
            "name": "Baxtiyorjon"
        }
    }


def save_users():
    try:
        with open(
            USERS_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                USERS_ROLES,
                f,
                ensure_ascii=False,
                indent=4
            )

    except Exception as e:
        print(f"Users saqlash xatosi: {e}")


USERS_ROLES = load_users()


def get_role(user_id):

    user = USERS_ROLES.get(
        str(user_id),
        {}
    )

    return user.get("role")


# ================= ACCESS TEKSHIRUV =================

def check_user_access(user_id: int) -> bool:

    user_info = USERS_ROLES.get(
        str(user_id)
    )

    if not user_info:
        return False

    if not isinstance(
        user_info,
        dict
    ):
        return False

    if user_info.get(
        "role"
    ) in [
        None,
        "rejected"
    ]:
        return False

    if user_info.get(
        "name"
    ) is None:
        return False

    return True

# Vazifalarni saqlash bazasi
TASKS_DATABASE = []

@start_router.message(CommandStart())
async def command_start_handler(message: types.Message):
    user_id = message.from_user.id
    user_info = USERS_ROLES.get(user_id)
    
    if isinstance(user_info, dict) and user_info.get("role") == "rejected":
        await message.answer("Assalomu alaykum. Afsuski, tizimdan foydalanish soʻrovingiz administrator tomonidan rad etilgan.")
        return

    if user_id not in USERS_ROLES:
        await message.answer(
            text="Assalomu alaykum, Edu_Control tizimiga xush kelibsiz!\n"
                 "Tizim administratoriga ruxsat soʻrovi yuborildi. Iltimos, soʻrovingiz tasdiqlanishini kuting. Rahmat!"
        )
        
        full_name = message.from_user.full_name
        if message.from_user.username:
            raw_username = message.from_user.username
            user_profile_link = f"https://t.me/{raw_username}"
            username_text = f"@{raw_username} (<a href='{user_profile_link}'>Profilga oʻtish</a>)"
        else:
            username_text = f"Mavjud emas (<a href='tg://user?id={user_id}'>Profilga oʻtish</a>)"
        
        admin_text = (
            f"🔔 <b>Yangi foydalanuvchi ruxsat soʻramoqda!</b>\n\n"
            f"👤 <b>Ism va familiya:</b> {full_name}\n"
            f"🆔 <b>ID raqami:</b> <code>{user_id}</code>\n"
            f"🌐 <b>Telegram sahifasi:</b> {username_text}\n\n"
            f"Iltimos, ushbu foydalanuvchiga tegishli unvonni (rol) bering yoki soʻrovni rad eting 👇"
        )
        
        try:
            await message.bot.send_message(
                chat_id=ADMIN_ID,
                text=admin_text,
                parse_mode="HTML",
                disable_web_page_preview=True,
                reply_markup=get_admin_approval_keyboard(user_id)
            )
        except Exception as e:
            print(f"❌ Administratorga xabar yuborishda muammo: {e}")
        return

    saved_name = user_info.get(
        "name",
        message.from_user.full_name
    )

    role = user_info.get("role")

    await message.answer(
        text=f"Assalomu alaykum, {saved_name}! "
             f"Tizimga xush kelibsiz.\n"
             f"Quyidagi tugmalar orqali botni boshqarishingiz mumkin 👇",

        reply_markup=get_main_menu(role)
    )


# ================= CALLBACK HANDLERS (ADMIN APPROVAL) =================

@start_router.callback_query(F.data.startswith("approve_"))
async def admin_approve_callback(call: types.CallbackQuery):
    try:
        data_parts = call.data.split("_")
        role = data_parts[1]
        target_user_id = int(data_parts[2])
        
        USERS_ROLES[str(target_user_id)] = {
            "role": role,
            "name": None
        }

        save_users()
        
        await call.message.edit_text(
            text=f"{call.message.text}\n\n✅ <b>Tasdiqlandi!</b> Foydalanuvchiga <b>{role}</b> unvoni muvaffaqiyatli berildi.",
            parse_mode="HTML"
        )
        
        user_text = f"Sizga administrator tomonidan \"{role}\" unvoni berildi. Iltimos, tizimda foydalanish uchun ism va familiyangizni kiriting:"
        await call.bot.send_message(
            chat_id=target_user_id,
            text=user_text,
            reply_markup=types.ReplyKeyboardRemove()  
        )
            
    except Exception as e:
        print(f"❌ Tasdiqlash jarayonida xatolik: {e}")
    await call.answer()


@start_router.callback_query(F.data.startswith("reject_"))
async def admin_reject_callback(call: types.CallbackQuery):
    try:
        target_user_id = int(call.data.split("_")[1])
        USERS_ROLES[str(target_user_id)] = {
            "role":"rejected",
            "name":None
        }

        save_users()
        
        await call.message.edit_text(
            text=f"{call.message.text}\n\n❌ <b>Soʻrov rad etildi!</b> Foydalanuvchi bloklandi.",
            parse_mode="HTML"
        )
        await call.bot.send_message(chat_id=target_user_id, text="Sizning botdan foydalanish soʻrovingiz administrator tomonidan rad etildi.")
    except Exception as e:
        print(f"❌ Rad etish jarayonida xatolik: {e}")
    await call.answer()


# ================= FOYDALANUVCHI ISMINI QABUL QILISH =================

@start_router.message(lambda msg: isinstance(USERS_ROLES.get(msg.from_user.id), dict) and USERS_ROLES.get(msg.from_user.id).get("name") is None)
async def get_user_real_name_handler(message: types.Message):
    user_id = message.from_user.id
    input_text = message.text.strip()
    first_name = input_text.split()[0]
    
    USERS_ROLES[str(user_id)]["name"] = input_text

    save_users()

    await message.answer(
        text=f"Hurmatli {first_name}, siz muvaffaqiyatli roʻyxatdan oʻtdingiz. "
             f"Endi bot imkoniyatlaridan foydalanishingiz mumkin.",

        reply_markup=get_main_menu(
            USERS_ROLES[str(user_id)]["role"]
        )
    )


# ================= VAZIFA YARATISH LOGIKASI =================

def check_user_access(user_id: int) -> bool:
    user_info = USERS_ROLES.get(user_id)
    if not user_info or not isinstance(user_info, dict): return False
    if user_info.get("role") in [None, "rejected"] or user_info.get("name") is None: return False
    return True

# 1-QADAM: Vazifa turi soʻraladi
@start_router.message(F.text == "➕ Vazifa qoʻshish")
async def add_task_handler(message: types.Message, state: FSMContext):
    if not check_user_access(message.from_user.id): return
    await message.answer(text="Qanday turdagi vazifa yaratmoqchisiz?", reply_markup=task_type_keyboard)

# 2-QADAM: Unvon (Boʻlim) soʻraladi
@start_router.message(F.text.in_(["Muntazam (Doimiy)", "Kunlik (Bir martalik)"]))
async def task_type_selected_handler(message: types.Message, state: FSMContext):
    if not check_user_access(message.from_user.id): return
    await state.update_data(task_type=message.text)
    await message.answer(text="Ushbu vazifa qaysi boʻlim/unvon xodimiga tegishli?", reply_markup=assign_role_keyboard)
    await state.set_state(TaskStates.waiting_for_target_role)

# 3-QADAM: Aniq mas'ul xodim tanlanadi
@start_router.message(TaskStates.waiting_for_target_role, F.text.in_(["Admin", "Kassir", "Sanitar", "Manager"]))
async def get_target_role_handler(message: types.Message, state: FSMContext):
    selected_role = message.text
    await state.update_data(target_role=selected_role)
    
    inline_kb = []
    found_users = False
    
    for u_id, u_info in USERS_ROLES.items():
        if isinstance(u_info, dict) and u_info.get("role") == selected_role and u_info.get("name"):
            found_users = True
            inline_kb.append([types.InlineKeyboardButton(text=u_info.get("name"), callback_data=f"assignuser_{u_id}")])
            
    if not found_users:
        await message.answer(text=f"⚠️ Diqqat! Tizimda hali tasdiqlangan va ismi kiritilgan '{selected_role}' xodimlari magenta emas!")
        return
        
    await message.answer(
        text=f"Aynan qaysi '{selected_role}' xodimiga ushbu vazifani biriktirmoqchisiz? Quyidagilardan tanlang 👇", 
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=inline_kb)
    )
    await state.set_state(TaskStates.waiting_for_target_user)

# 4-QADAM: Vazifa nomi soʻraladi
@start_router.callback_query(TaskStates.waiting_for_target_user, F.data.startswith("assignuser_"))
async def process_target_user_callback(call: types.CallbackQuery, state: FSMContext):
    target_user_id = int(call.data.split("_")[1])
    employee_name = USERS_ROLES.get(target_user_id, {}).get("name", "Noma'lum xodim")
    
    await state.update_data(assigned_to_id=target_user_id, assigned_to_name=employee_name)
    
    await call.message.delete()
    await call.message.answer(text="Iltimos, vazifa nomini kiriting:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(TaskStates.waiting_for_name)
    await call.answer()

# 5-QADAM: TARMOQLANISH (Kunlik boʻlsa izohga, Muntazam boʻlsa kunlarga oʻtadi)
@start_router.message(TaskStates.waiting_for_name)
async def get_task_name_handler(message: types.Message, state: FSMContext):
    await state.update_data(task_name=message.text.strip())
    user_data = await state.get_data()
    
    if user_data.get("task_type") == "Kunlik (Bir martalik)":
        await message.answer(text="Izoh (bu yerda admin tomonidan yozilgan taskning izohi):")
        await state.set_state(TaskStates.waiting_for_description)
    else:
        await message.answer(text="Vazifa haftaning qaysi kunlari foydalanuvchiga koʻrinsin?", reply_markup=days_keyboard)
        await state.set_state(TaskStates.waiting_for_days)

# 🌟 YANGI QADAM: Kunlik vazifaning izohini qabul qilish va isbot turiga oʻtkazish
@start_router.message(TaskStates.waiting_for_description)
async def get_task_description_handler(message: types.Message, state: FSMContext):
    await state.update_data(task_description=message.text.strip())
    await message.answer(text="Ushbu vazifani yakunlash uchun qanday turdagi isbot talab etiladi?", reply_markup=proof_type_keyboard)
    await state.set_state(TaskStates.waiting_for_proof_type)


# ================= DOIMIY (MUNTAZAM) VAZIFA KUN / VAQT LOGIKALARI =================

# 6-QADAM (A-variant): Standart kunlar tanlanganda
@start_router.message(TaskStates.waiting_for_days, F.text.in_(["Toq kunlar", "Juft kunlar", "Haftada 6 kun"]))
async def get_task_days_handler(message: types.Message, state: FSMContext):
    day_mapping = {"Toq kunlar": "ODD", "Juft kunlar": "EVEN", "Haftada 6 kun": "6 days a week"}
    await state.update_data(task_days=day_mapping.get(message.text))
    await message.answer(text="Vazifa kuniga necha marta koʻrinishi kerak?", reply_markup=frequency_keyboard)
    await state.set_state(TaskStates.waiting_for_frequency)

# 6-QADAM (B-variant): Maxsus kunlar (Inline)
@start_router.message(TaskStates.waiting_for_days, F.text == "Boshqa kunlar")
async def other_days_handler(message: types.Message, state: FSMContext):
    await state.update_data(selected_days=[])
    await message.answer(text="Iltimos, kerakli hafta kunlarini bittalab tanlang:", reply_markup=get_inline_days_keyboard([]))

@start_router.callback_query(TaskStates.waiting_for_days, F.data.startswith("day_"))
async def toggle_day_callback(call: types.CallbackQuery, state: FSMContext):
    day_code = call.data.split("_")[1]
    user_data = await state.get_data()
    selected_days = user_data.get("selected_days", [])
    if day_code in selected_days: selected_days.remove(day_code)
    else: selected_days.append(day_code)
    await state.update_data(selected_days=selected_days)
    await call.message.edit_reply_markup(reply_markup=get_inline_days_keyboard(selected_days))
    await call.answer()

@start_router.callback_query(TaskStates.waiting_for_days, F.data == "days_done")
async def days_done_callback(call: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    selected_days = user_data.get("selected_days", [])
    if not selected_days:
        await call.answer(text="Iltimos, kamida bitta kunni tanlang!", show_alert=True)
        return
    await state.update_data(task_days=", ".join(selected_days))
    await call.message.delete()
    await call.message.answer(text="Vazifa kuniga necha marta koʻrinishi kerak?", reply_markup=frequency_keyboard)
    await state.set_state(TaskStates.waiting_for_frequency)
    await call.answer()

# 7-QADAM (1-variant): Kuniga 1 marta
@start_router.message(TaskStates.waiting_for_frequency, F.text == "Kuniga 1 marta")
async def once_frequency_handler(message: types.Message, state: FSMContext):
    await state.update_data(task_frequency="Once")
    await message.answer(
        text="Vazifa xodimga qaysi vaqtda yuborilsin?\n\n<b>Format shabloni:</b> <code>11:33</code> koʻrinishida kiriting.", 
        parse_mode="HTML", 
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(TaskStates.waiting_for_once_time)

@start_router.message(TaskStates.waiting_for_once_time)
async def get_once_time_handler(message: types.Message, state: FSMContext):
    await state.update_data(task_times=message.text.strip())
    await message.answer(text="Ushbu vazifani yakunlash uchun qanday turdagi isbot talab etiladi?", reply_markup=proof_type_keyboard)
    await state.set_state(TaskStates.waiting_for_proof_type)

# 7-QADAM (2-variant): Bir necha marta
@start_router.message(TaskStates.waiting_for_frequency, F.text == "Bir necha marta")
async def multiple_frequency_handler(message: types.Message, state: FSMContext):
    await state.update_data(task_frequency="Multiple times")
    await message.answer(
        text="Vazifa xodimga qaysi vaqtlarda yuborilsin?\n\n<b>Format shabloni:</b> Vaqtlarni vergul bilan ajratib yozing.\nMasalan: <code>08:00, 14:00, 18:00</code>", 
        parse_mode="HTML", 
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(TaskStates.waiting_for_multiple_times)

@start_router.message(TaskStates.waiting_for_multiple_times)
async def get_multiple_times_handler(message: types.Message, state: FSMContext):
    await state.update_data(task_times=message.text.strip())
    await message.answer(text="Ushbu vazifani yakunlash uchun qanday turdagi isbot talab etiladi?", reply_markup=proof_type_keyboard)
    await state.set_state(TaskStates.waiting_for_proof_type)


# ================= FINAL: VAZIFANI YARATISH VA MAS'ULGA YUBORISH =================

@start_router.message(TaskStates.waiting_for_proof_type, F.text.in_(["Dumaloq video", "Rasm yuborish"]))
async def finalize_task_creation_handler(message: types.Message, state: FSMContext):
    proof_mapping = {"Dumaloq video": "Video message", "Rasm yuborish": "Photo"}
    
    user_data = await state.get_data()
    task_id = len(TASKS_DATABASE) + 1
    
    is_daily = user_data.get("task_type") == "Kunlik (Bir martalik)"
    raw_times = user_data.get("task_times", "")
    times_list = [t.strip() for t in raw_times.split(",") if t.strip()] if not is_daily else []
    
    new_task = {
        "id": task_id,
        "task_type": user_data.get("task_type"),
        "task_name": user_data.get("task_name"),
        "task_description": user_data.get("task_description", "Mavjud emas"), # Faqat kunlikda bo'ladi
        "task_days": user_data.get("task_days", "Kunlik vazifa"), 
        "task_frequency": user_data.get("task_frequency", "Bir martalik"),
        "task_times": times_list,
        "proof_type": proof_mapping.get(message.text),
        "assigned_to_id": user_data.get("assigned_to_id"),
        "assigned_to_name": user_data.get("assigned_to_name"),
        "sent_today_times": [] 
    }
    
    TASKS_DATABASE.append(new_task)
    
    # Administrator hisoboti
    report_text = (
        f"🎉 <b>Yangi vazifa muvaffaqiyatli yaratildi!</b>\n\n"
        f"📋 <b>Turi:</b> {new_task['task_type']}\n"
        f"📌 <b>Nomi:</b> {new_task['task_name']}\n"
    )
    if is_daily:
        report_text += f"📝 <b>Izoh:</b> {new_task['task_description']}\n"
    else:
        report_text += (
            f"📅 <b>Amal qilish kunlari:</b> {new_task['task_days']}\n"
            f"🔢 <b>Takrorlanish chastotasi:</b> {new_task['task_frequency']}\n"
            f"⏰ <b>Belgilangan vaqt(lar)i:</b> {', '.join(new_task['task_times'])}\n"
        )
    report_text += (
        f"📸 <b>Talab etiladigan isbot:</b> {message.text}\n"
        f"👤 <b>Masʻul xodim:</b> {new_task['assigned_to_name']}"
    )
    
    await message.answer(text=report_text, parse_mode="HTML")
    await message.answer(text="Asosiy menyuga qaytdingiz.", reply_markup=main_menu_keyboard)
    
    # Xodimga xabar yuborish qismi (Kunlik bo'lsa darhol inline tugma bilan boradi)
    try:
        if is_daily:
            employee_text = (
                f"🔔 <b>Sizga yangi kunlik vazifa yuklatildi!</b>\n\n"
                f"📌 <b>Vazifa nomi:</b> {new_task['task_name']}\n"
                f"📝 <b>Izoh (Admin eslatmasi):</b> {new_task['task_description']}\n\n"
                f"Vazifani bajarib, pastdagi tugma orqali hisobot (isbot) yuboring 👇"
            )
            await message.bot.send_message(
                chat_id=new_task["assigned_to_id"],
                text=employee_text,
                parse_mode="HTML",
                reply_markup=get_task_complete_keyboard(new_task["id"])
            )
        else:
            await message.bot.send_message(
                chat_id=new_task["assigned_to_id"],
                text=f"🔔 <b>Sizga yangi muntazam vazifa yuklatildi!</b>\n\n"
                     f"📌 <b>Vazifa nomi:</b> {new_task['task_name']}\n"
                     f"⏰ <b>Belgilangan vaqt(lar)i:</b> {', '.join(new_task['task_times'])}",
                parse_mode="HTML"
            )
    except Exception as e:
        print(f"Xodimga bildirishnoma yuborishda xatolik: {e}")
        
    await state.clear()


# ================= VAZIFALAR ROʻYXATINI KOʻRISH =================

@start_router.message(F.text == "📋 Vazifalar roʻyxati")
async def list_tasks_handler(message: types.Message):
    if not check_user_access(message.from_user.id): return
    if not TASKS_DATABASE:
        await message.answer(text="📭 Hozircha tizimda hech qanday faol vazifalar magenta emas.")
        return
        
    response_text = "📋 <b>Tizimdagi joriy faol vazifalar roʻyxati:</b>\n\n"
    for idx, task in enumerate(TASKS_DATABASE, 1):
        if task.get("task_type") == "Kunlik (Bir martalik)":
            response_text += (
                f"{idx}. <b>[KUNLIK] {task['task_name']}</b>\n"
                f"   👤 Masʻul: {task['assigned_to_name']}\n"
                f"   📝 Izoh: {task['task_description']}\n"
                f"   📸 Isbot: {task['proof_type']}\n\n"
            )
        else:
            response_text += (
                f"{idx}. <b>[DOIMIY] {task['task_name']}</b>\n"
                f"   👤 Masʻul: {task['assigned_to_name']}\n"
                f"   ⏰ Vaqti: {', '.join(task['task_times'])}\n"
                f"   📅 Kunlar: {task['task_days']}\n"
                f"   📸 Isbot: {task['proof_type']}\n\n"
            )
    await message.answer(text=response_text, parse_mode="HTML")


# ================= XODIM VAZIFANI BAJARISH BOSQICHI =================

@start_router.callback_query(F.data.startswith("completetask_"))
async def employee_complete_task_callback(call: types.CallbackQuery, state: FSMContext):
    task_id = int(call.data.split("_")[1])
    task = next((t for t in TASKS_DATABASE if t["id"] == task_id), None)
    if not task:
        await call.answer(text="Kechirasiz, ushbu vazifa tizimdan topilmadi yoki oʻchirilgan!", show_alert=True)
        return
        
    await state.update_data(active_task_id=task_id, proof_required=task["proof_type"])
    
    if task["proof_type"] == "Photo":
        await call.message.answer(text="Ushbu vazifani tasdiqlash uchun iltimos, <b>Rasm (Photo)</b> yuboring!", parse_mode="HTML")
    else:
        await call.message.answer(text="Ushbu vazifani tasdiqlash uchun iltimos, <b>Dumaloq video (Video message)</b> yuboring!", parse_mode="HTML")
        
    await state.set_state(TaskStates.waiting_for_task_proof)
    await call.answer()


# ================= XODIM ISBOTINI GURUHGA YUBORISH =================

@start_router.message(TaskStates.waiting_for_task_proof)
async def receive_task_proof_handler(message: types.Message, state: FSMContext):
    state_data = await state.get_data()
    proof_required = state_data.get("proof_required")
    task_id = state_data.get("active_task_id")
    
    global TASKS_DATABASE
    task = next((t for t in TASKS_DATABASE if t["id"] == task_id), None)
    GROUP_CHAT_ID = -5226036627  
    
    if proof_required == "Photo" and message.photo:
        await message.answer(text="Vazifa muvaffaqiyatli topshirildi va hisobot guruhga yuborildi.", reply_markup=main_menu_keyboard)
        if task:
            group_text = (
                f"✅ <b>VAZIFA BAJARILDI!</b>\n\n"
                f"📋 <b>Turi:</b> {task['task_type']}\n"
                f"📌 <b>Vazifa nomi:</b> {task['task_name']}\n"
                f"👤 <b>Masʻul xodim:</b> {task['assigned_to_name']}\n"
                f"📸 <b>Isbot turi:</b> Rasm (Photo)\n"
                f"⏰ <b>Topshirilgan vaqt:</b> {datetime.now(timezone(timedelta(hours=5))).strftime('%H:%M')}"
            )
            await message.bot.send_message(chat_id=GROUP_CHAT_ID, text=group_text, parse_mode="HTML")
            await message.bot.send_photo(chat_id=GROUP_CHAT_ID, photo=message.photo[-1].file_id)
            
            # Kunlik bir martalik vazifa bajarilgach ro'yxatdan o'chadi
            if task.get("task_type") == "Kunlik (Bir martalik)":
                TASKS_DATABASE = [t for t in TASKS_DATABASE if t["id"] != task_id]
        await state.clear()
        
    elif proof_required == "Video message" and message.video_note:
        await message.answer(text="Vazifa muvaffaqiyatli topshirildi va hisobot guruhga yuborildi.", reply_markup=main_menu_keyboard)
        if task:
            group_text = (
                f"✅ <b>VAZIFA BAJARILDI!</b>\n\n"
                f"📋 <b>Turi:</b> {task['task_type']}\n"
                f"📌 <b>Vazifa nomi:</b> {task['task_name']}\n"
                f"👤 <b>Masʻul xodim:</b> {task['assigned_to_name']}\n"
                f"📸 <b>Isbot turi:</b> Dumaloq video (Video message)\n"
                f"⏰ <b>Topshirilgan vaqt:</b> {datetime.now(timezone(timedelta(hours=5))).strftime('%H:%M')}"
            )
            await message.bot.send_message(chat_id=GROUP_CHAT_ID, text=group_text, parse_mode="HTML")
            await message.bot.send_video_note(chat_id=GROUP_CHAT_ID, video_note=message.video_note.file_id)
            
            if task.get("task_type") == "Kunlik (Bir martalik)":
                TASKS_DATABASE = [t for t in TASKS_DATABASE if t["id"] != task_id]
        await state.clear()
        
    else:
        if proof_required == "Photo":
            await message.answer(text="⚠️ Notoʻgʻri format! Iltimos, ushbu vazifa uchun faqat <b>Rasm (Photo)</b> yuboring.", parse_mode="HTML")
        else:
            await message.answer(text="⚠️ Notoʻgʻri format! Iltimos, ushbu vazifa uchun faqat <b>Dumaloq video (Video message)</b> yuboring.", parse_mode="HTML")


# ================= TAYMER (FAQAT MUNTAZAM VAZIFALAR UCHUN) =================

async def auto_task_scheduler(bot):
    last_checked_minute = ""
    tashkent_tz = timezone(timedelta(hours=5))
    
    while True:
        try:
            now = datetime.now(timezone.utc).astimezone(tashkent_tz)
            current_time_str = now.strftime("%H:%M")
            current_day_name = now.strftime("%a").strip().lower() 
            day_of_month = now.day
            
            if current_time_str == "00:00":
                for task in TASKS_DATABASE:
                    task["sent_today_times"] = []
            
            if current_time_str != last_checked_minute:
                for task in TASKS_DATABASE:
                    # Kunlik vazifalar avtomatik taymer orqali qayta yuborilmaydi (ular bir martalik)
                    if task.get("task_type") == "Kunlik (Bir martalik)":
                        continue
                        
                    if current_time_str in task["task_times"] and current_time_str not in task["sent_today_times"]:
                        day_match = False
                        task_days = str(task["task_days"]).strip()
                        
                        if task_days == "ODD" and day_of_month % 2 != 0:
                            day_match = True
                        elif task_days == "EVEN" and day_of_month % 2 == 0:
                            day_match = True
                        elif task_days == "6 days a week" and current_day_name != "sun":
                            day_match = True
                        else:
                            clean_days = [d.strip().lower() for d in task_days.split(",") if d.strip()]
                            if current_day_name in clean_days:
                                day_match = True
                        
                        if day_match:
                            text_to_employee = f"📌 <b>{task['task_name']}</b>"
                            await bot.send_message(
                                chat_id=task["assigned_to_id"],
                                text=text_to_employee,
                                parse_mode="HTML",
                                reply_markup=get_task_complete_keyboard(task["id"])
                            )
                            task["sent_today_times"].append(current_time_str)
                last_checked_minute = current_time_str
        except Exception as e:
            print(f"Taymer tizimida xato: {e}")
        await asyncio.sleep(5)


# ================= VAZIFANI O'CHIRISH LOGIKASI =================

@start_router.message(F.text == "🗑 Vazifani oʻchirish")
async def remove_task_menu_handler(message: types.Message):
    if not check_user_access(message.from_user.id): return
    if not TASKS_DATABASE:
        await message.answer(text="📭 Hozircha tizimda hech qanday faol vazifalar magenta emas.")
        return
        
    await message.answer(
        text="🗑 <b>Oʻchirmoqchi boʻlgan vazifangizni tanlang:</b>\n<i>(Tugma bosilishi bilan vazifa bazadan butunlay oʻchadi!)</i>",
        parse_mode="HTML",
        reply_markup=get_remove_tasks_keyboard(TASKS_DATABASE)
    )

@start_router.callback_query(F.data.startswith("removetask_"))
async def process_remove_task_callback(call: types.CallbackQuery):
    task_id = int(call.data.split("_")[1])
    global TASKS_DATABASE
    task_to_remove = next((t for t in TASKS_DATABASE if t["id"] == task_id), None)
    
    if task_to_remove:
        TASKS_DATABASE = [t for t in TASKS_DATABASE if t["id"] != task_id]
        await call.message.edit_text(
            text=f"🗑 <b>Vazifa muvaffaqiyatli oʻchirildi!</b>\n\n📌 <b>Nomi:</b> {task_to_remove['task_name']}\n👤 <b>Masʻul boʻlgan xodim:</b> {task_to_remove['assigned_to_name']}",
            parse_mode="HTML"
        )
    else:
        await call.answer(text="⚠️ Bu vazifa allaqachon oʻchirilgan yoki topilmadi!", show_alert=True)
    await call.answer()

@start_router.callback_query(F.data == "remove_cancel")
async def cancel_remove_callback(call: types.CallbackQuery):
    await call.message.delete()
    await call.message.answer(text="Oʻchirish jarayoni bekor qilindi.", reply_markup=main_menu_keyboard)
    await call.answer()

# ==============================================================================
# 🌟 YANGI INTEGRATSIYA: XODIMLAR PANELINI MATN SIFATIDA CHIQARISH VA TAHRIRLASH
# ==============================================================================

# 1. "Xodimlar" tugmasi bosilganda ro'yxatni CHATga matn ko'rinishida chiqarish
@start_router.message(F.text == "👥 Xodimlar")
async def view_employees_handler(message: types.Message):
    if not check_user_access(message.from_user.id): return
    
    # Faqat ismi kiritilgan va tizimda rad etilmagan faol xodimlarni saralash (Asosiy Admin ro'yxatda chiqmaydi)
    active_staff = {
        u_id: u_info for u_id, u_info in USERS_ROLES.items() 
        if isinstance(u_info, dict) and u_info.get("name") and u_info.get("role") != "rejected" and u_id != ADMIN_ID
    }
    
    if not active_staff:
        await message.answer(text="📭 Hozircha tizimda birorta ham tasdiqlangan xodim mavjud emas.")
        return
        
    response_text = "👥 <b>Tizimdagi joriy xodimlar roʻyxati:</b>\n\n"
    inline_kb = []
    
    for idx, (u_id, u_info) in enumerate(active_staff.items(), 1):
        # Matn ko'rinishida ism-familiya va lavozimi chatga chiqadi
        response_text += f"{idx}. 👤 <b>{u_info['name']}</b> — 🎖 <i>{u_info['role']}</i>\n"
        # Tahrirlash tugmasini pastdan chiroyli inline ko'rinishda taqdim etamiz
        inline_kb.append([types.InlineKeyboardButton(text=f"⚙️ {u_info['name']}", callback_data=f"editstaff_{u_id}")])
        
    response_text += "\n<i>Tahrirlash yoki botdan chetlashtirish uchun quyidagi tugmalardan kerakli xodimni tanlang:</i>"
    
    await message.answer(
        text=response_text, 
        parse_mode="HTML", 
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=inline_kb)
    )


# 2. Ro'yxatdagi xodim ustiga bosilganda variantlarni ko'rsatish (Lavozim yoki Chetlashtirish)
@start_router.callback_query(F.data.startswith("editstaff_"))
async def process_edit_staff_callback(call: types.CallbackQuery, state: FSMContext):
    target_user_id = int(call.data.split("_")[1])
    staff_info = USERS_ROLES.get(target_user_id)
    
    if not staff_info:
        await call.answer(text="⚠️ Bu xodim tizimdan topilmadi!", show_alert=True)
        return
        
    options_kb = [
        [
            types.InlineKeyboardButton(text="🎖 Lavozimni o'zgartirish", callback_data=f"rolechange_{target_user_id}"),
            types.InlineKeyboardButton(text="❌ Botdan chetlashtirish", callback_data=f"firestaff_{target_user_id}")
        ],
        [types.InlineKeyboardButton(text="⬅️ Orqaga", callback_data="editstaff_cancel")]
    ]
    
    await call.message.edit_text(
        text=f"👤 <b>Xodim:</b> {staff_info['name']}\n🎖 <b>Joriy lavozimi:</b> {staff_info['role']}\n\n"
             f"Ushbu xodim ustida qanday amal bajarmoqchisiz? 👇",
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=options_kb)
    )
    await call.answer()


# 3. Lavozimni o'zgartirish tugmasi bosilganda tizimdagi barcha rollarni ko'rsatish
@start_router.callback_query(F.data.startswith("rolechange_"))
async def process_role_change_menu(call: types.CallbackQuery):
    target_user_id = int(call.data.split("_")[1])
    
    # Tizimingizdagi joriy rollar ro'yxati
    roles = ["Admin", "Kassir", "Sanitar", "Manager"]
    inline_kb = []
    row = []
    
    for r in roles:
        row.append(types.InlineKeyboardButton(text=r, callback_data=f"setnewrole_{r}_{target_user_id}"))
        if len(row) == 2:
            inline_kb.append(row)
            row = []
            
    inline_kb.append([types.InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"editstaff_{target_user_id}")])
    
    await call.message.edit_text(
        text="⚙️ Xodim uchun <b>yangi lavozimni</b> tanlang:",
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=inline_kb)
    )
    await call.answer()


# 4. Yangi lavozim tanlanganda bazada saqlash va xodimga bildirishnoma yuborish
@start_router.callback_query(F.data.startswith("setnewrole_"))
async def save_new_role_callback(call: types.CallbackQuery, state: FSMContext):
    data_parts = call.data.split("_")
    new_role = data_parts[1]
    target_user_id = int(data_parts[2])
    
    if target_user_id in USERS_ROLES:
        USERS_ROLES[str(target_user_id)]["role"] = new_role

        save_users()
        staff_name = USERS_ROLES[str(target_user_id)]["name"]
        
        await call.message.edit_text(
            text=f"✅ <b>Muvaffaqiyatli oʻzgartirildi!</b>\n\n"
                 f"👤 Xodim: <b>{staff_name}</b>\n"
                 f"🎖 Yangi lavozimi: <b>{new_role}</b>",
            parse_mode="HTML"
        )
        
        # Xodimning o'ziga ham unvoni o'zgargani haqida ogohlantirish xabari yuboramiz
        try:
            await call.bot.send_message(
                chat_id=target_user_id,
                text=f"🔔 <b>Diqqat!</b> Administrator tomonidan sizning lavozimingiz <b>{new_role}</b> etib belgilandi.",
                parse_mode="HTML",
                reply_markup=main_menu_keyboard
            )
        except Exception as e:
            print(f"Xodimni rolda ogohlantirishda xatolik: {e}")
    else:
        await call.answer(text="⚠️ Xatolik: Xodim topilmadi!", show_alert=True)
        
    await state.clear()
    await call.answer()


# 5. Xodimni botdan butunlay chetlashtirish (Block qilish)
@start_router.callback_query(F.data.startswith("firestaff_"))
async def fire_staff_callback(call: types.CallbackQuery, state: FSMContext):
    target_user_id = int(call.data.split("_")[1])
    
    if target_user_id in USERS_ROLES:
        staff_name = USERS_ROLES[str(target_user_id)]["name"]
        
        # Rolni 'rejected' holatiga o'tkazish orqali kirish imkoniyatini yopamiz
        USERS_ROLES[str(target_user_id)]["role"]="rejected"

        save_users()
        
        await call.message.edit_text(
            text=f"❌ <b>Xodim botdan chetlashtirildi!</b>\n\n"
                 f"👤 <b>{staff_name}</b> endi tizimga kira olmaydi va unga avtomatik vazifalar yuborilmaydi.",
            parse_mode="HTML"
        )
        
        # Chetlashtirilgan xodimga darhol bloklangan xabarini yuborib klaviaturasini tozalaymiz
        try:
            await call.bot.send_message(
                chat_id=target_user_id,
                text="❌ <b>Siz administrator tomonidan Edu_Control tizimidan chetlashtirildingiz!</b>",
                parse_mode="HTML",
                reply_markup=types.ReplyKeyboardRemove()
            )
        except Exception as e:
            print(f"Xodimga chetlashtirish xabarini yuborishda xatolik: {e}")
    else:
        await call.answer(text="⚠️ Xodim topilmadi!", show_alert=True)
        
    await state.clear()
    await call.answer()


# 6. Tahrirlashni bekor qilish / Orqaga qaytish
@start_router.callback_query(F.data == "editstaff_cancel")
async def cancel_edit_staff_callback(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer(text="Xodimlarni boshqarish paneli yopildi.", reply_markup=main_menu_keyboard)
    await state.clear()
    await call.answer()

# ==============================================================================
# 🌟 YANGI INTEGRATSIYA: ARXIV PANELINI BOSHQARISH VA QAYTA FAOLLASHTIRISH
# ==============================================================================

# 1. "Arxiv" tugmasi bosilganda chetlashtirilgan/rad etilganlarni chatga chiqarish
@start_router.message(F.text == "🗄 Arxiv")
async def view_archive_handler(message: types.Message):
    if not check_user_access(message.from_user.id): return
    
    # Faqat 'rejected' (rad etilgan yoki chetlashtirilgan) foydalanuvchilarni saralash
    archived_users = {
        u_id: u_info for u_id, u_info in USERS_ROLES.items()
        if isinstance(u_info, dict) and u_info.get("role") == "rejected"
    }
    
    if not archived_users:
        await message.answer(text="📭 Arxiv boʻsh. Chetlashtirilgan yoki rad etilgan foydalanuvchilar mavjud emas.")
        return
        
    response_text = "🗄 <b>Arxivdagi foydalanuvchilar roʻyxati:</b>\n\n"
    inline_kb = []
    
    for idx, (u_id, u_info) in enumerate(archived_users.items(), 1):
        # Agar foydalanuvchi ismi hali kiritilmasdan rad etilgan bo'lsa, "Yangi so'rovchi" deb ko'rsatiladi
        display_name = u_info.get("name") if u_info.get("name") else f"Foydalanuvchi [ID: {u_id}]"
        
        response_text += f"{idx}. ❌ <b>{display_name}</b> — <i>Tizimdan chetlashtirilgan</i>\n"
        # Qayta faollashtirish tugmasini generatsiya qilamiz
        inline_kb.append([types.InlineKeyboardButton(text=f"🔄 {display_name}", callback_data=f"restorestaff_{u_id}")])
        
    response_text += "\n<i>Ushbu foydalanuvchilarni qayta faollashtirish va lavozim berish uchun mos tugmani bosing:</i>"
    
    await message.answer(
        text=response_text,
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=inline_kb)
    )


# 2. Arxivdagi xodim bosilganda unga yangi lavozim tanlash menyusini ochish
@start_router.callback_query(F.data.startswith("restorestaff_"))
async def process_restore_staff_callback(call: types.CallbackQuery):
    target_user_id = int(call.data.split("_")[1])
    user_info = USERS_ROLES.get(target_user_id)
    
    if not user_info:
        await call.answer(text="⚠️ Bu foydalanuvchi ma'lumotlar bazasidan topilmadi!", show_alert=True)
        return
        
    display_name = user_info.get("name") if user_info.get("name") else f"Foydalanuvchi [{target_user_id}]"
    
    # Tizimdagi mavjud faol rollar ro'yxati
    roles = ["Admin", "Kassir", "Sanitar", "Manager"]
    inline_kb = []
    row = []
    
    for r in roles:
        row.append(types.InlineKeyboardButton(text=r, callback_data=f"savearchiverole_{r}_{target_user_id}"))
        if len(row) == 2:
            inline_kb.append(row)
            row = []
            
    inline_kb.append([types.InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="editstaff_cancel")])
    
    await call.message.edit_text(
        text=f"🔄 <b>Foydalanuvchi:</b> {display_name}\n\n"
             f"Ushbu xodimni faollashtirish uchun <b>yangi lavozimni (rol)</b> tanlang:",
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=inline_kb)
    )
    await call.answer()


# 3. Lavozim tanlangach arxivdan chiqarish, saqlash va unga xabarnoma yuborish
@start_router.callback_query(F.data.startswith("savearchiverole_"))
async def save_archive_role_callback(call: types.CallbackQuery, state: FSMContext):
    data_parts = call.data.split("_")
    new_role = data_parts[1]
    target_user_id = int(data_parts[2])
    
    if target_user_id in USERS_ROLES:
        # Rolni yangilaymiz (Arxivdan avtomatik chiqadi)
        USERS_ROLES[str(target_user_id)]["role"]=new_role

        save_users()
        
        # Agar foydalanuvchining ismi avval kiritilmagan bo'lsa, ism so'rash bosqichiga tayyorlaymiz
        has_name = USERS_ROLES[str(target_user_id)].get("name") is not None
        display_name = USERS_ROLES[str(target_user_id)]["name"] if has_name else "Xodim"
        
        await call.message.edit_text(
            text=f"✅ <b>Muvaffaqiyatli tiklandi!</b>\n\n"
                 f"👤 Xodim: <b>{display_name}</b>\n"
                 f"🎖 Yangi biriktirilgan lavozim: <b>{new_role}</b>\n\n"
                 f"<i>Xodimga tizim qayta faollashtirilgani haqida xabarnoma yuborildi.</i>",
            parse_mode="HTML"
        )
        
        # Tiklangan xodimning o'ziga xushxabarni va menyuni yuboramiz
        try:
            if has_name:
                # Ismi bor bo'lsa to'g'ridan to'g'ri asosiy menyu
                await call.bot.send_message(
                    chat_id=target_user_id,
                    text=f"🎉 <b>Xushxabar!</b> Administrator sizni arxivdan chiqardi va joriy lavozimingizni <b>{new_role}</b> etib belgiladi.\n"
                         f"Bot imkoniyatlaridan toʻliq foydalanishingiz mumkin!",
                    parse_mode="HTML",
                    reply_markup=main_menu_keyboard
                )
            else:
                # Ismi yo'q bo'lsa oldingi mantiq asosida ism so'raymiz
                await call.bot.send_message(
                    chat_id=target_user_id,
                    text=f"🎉 <b>Xushxabar!</b> Administrator sizning ruxsat soʻrovingizni tasdiqladi va <b>{new_role}</b> unvonini berdi.\n"
                         f"Iltimos, tizimdan foydalanish uchun ism va familiyangizni kiriting:",
                    parse_mode="HTML",
                    reply_markup=types.ReplyKeyboardRemove()
                )
        except Exception as e:
            print(f"Arxivdan tiklangan xodimga xabar yuborishda xatolik: {e}")
    else:
        await call.answer(text="⚠️ Tizim xatoligi yuz berdi!", show_alert=True)
        
    await state.clear()
    await call.answer()

from Handlers.states import AdminSalaryStates
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# ==============================================================================
# 🌟 ESKI PROYEKTDAN TUZATILGAN ADMIN OYLIK TO'LIQ TUGMALAR ZANJIRI (MUKAMMAL)
# ==============================================================================
from Handlers.states import AdminSalaryStates
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Ichki vaqtinchalik klaviatura funksiyalari (aiogram 3.x)
def get_status_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="NOVA"), KeyboardButton(text="PRIME")],
        [KeyboardButton(text="APEX"), KeyboardButton(text="LEADER")],
        [KeyboardButton(text="🏠 Bosh sahifa")]
    ], resize_keyboard=True)

def get_hours_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="6"), KeyboardButton(text="7"), KeyboardButton(text="8")],
        [KeyboardButton(text="✍️ Boshqa")],
        [KeyboardButton(text="🏠 Bosh sahifa"), KeyboardButton(text="⬅️ Ortga")]
    ], resize_keyboard=True)

def get_days_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="24"), KeyboardButton(text="25")],
        [KeyboardButton(text="26"), KeyboardButton(text="27")],
        [KeyboardButton(text="✍️ Boshqa")],
        [KeyboardButton(text="🏠 Bosh sahifa"), KeyboardButton(text="⬅️ Ortga")]
    ], resize_keyboard=True)

def get_yes_no_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="✅ HA"), KeyboardButton(text="❌ YO‘Q")],
        [KeyboardButton(text="🏠 Bosh sahifa"), KeyboardButton(text="⬅️ Ortga")]
    ], resize_keyboard=True)

def get_manual_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🏠 Bosh sahifa"), KeyboardButton(text="⬅️ Ortga")]
    ], resize_keyboard=True)


# 1. Asosiy menyudan "Admin oylik" bosilganda boshlanishi
@start_router.message(F.text == "📊 Admin oylik")
async def start_admin_salary_calc(message: types.Message, state: FSMContext):
    if not check_user_access(message.from_user.id): return
    await state.set_state(AdminSalaryStates.status)
    await message.answer("🏅 Status tanlang:", reply_markup=get_status_keyboard())

# Global tekshiruv: Har qanday bosqichda "Bosh sahifa" bosilsa bekor qilish
@start_router.message(AdminSalaryStates(), F.text == "🏠 Bosh sahifa")
async def back_to_home_salary(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Bosh sahifaga qaytdingiz.", reply_markup=main_menu_keyboard)

# 2. Status tanlanganda -> Soat so'rash va statusni saqlash
@start_router.message(AdminSalaryStates.status)
async def process_status(message: types.Message, state: FSMContext):
    if message.text not in ["NOVA", "PRIME", "APEX", "LEADER"]:
        return await message.answer("❌ Iltimos, tugmalardan birini tanlang:")
        
    await state.update_data(status=message.text.lower())
    await state.set_state(AdminSalaryStates.daily_hours)
    await message.answer("⏰ Kunlik ish soatini tanlang:", reply_markup=get_hours_keyboard())

# 3. Kunlik soat tanlanganda -> Kun so'rash
@start_router.message(AdminSalaryStates.daily_hours)
async def process_hours(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(AdminSalaryStates.status)
        return await message.answer("🏅 Status tanlang:", reply_markup=get_status_keyboard())
        
    if message.text == "✍️ Boshqa":
        await state.set_state(AdminSalaryStates.custom_daily_hours)
        return await message.answer("⏰ Soatni o'zingiz kiriting:", reply_markup=get_manual_keyboard())

    if not message.text.isdigit():
        return await message.answer("❌ Iltimos, to'g'ri soatni tanlang yoki raqam kiriting:")

    await state.update_data(daily_hours=int(message.text))
    await state.set_state(AdminSalaryStates.worked_days)
    await message.answer("📅 Ishlagan kunni tanlang:", reply_markup=get_days_keyboard())

# 3a. Custom soat kiritilganda -> Kun so'rash
@start_router.message(AdminSalaryStates.custom_daily_hours)
async def process_custom_hours(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(AdminSalaryStates.daily_hours)
        return await message.answer("⏰ Kunlik ish soatini tanlang:", reply_markup=get_hours_keyboard())

    if not message.text.isdigit():
        return await message.answer("❌ Iltimos, faqat raqam kiriting (Masalan: 8):")

    await state.update_data(daily_hours=int(message.text))
    await state.set_state(AdminSalaryStates.worked_days)
    await message.answer("📅 Ishlagan kunni tanlang:", reply_markup=get_days_keyboard())

# 4. Kun tanlanganda -> IELTS so'rash
@start_router.message(AdminSalaryStates.worked_days)
async def process_days(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(AdminSalaryStates.daily_hours)
        return await message.answer("⏰ Kunlik ish soatini tanlang:", reply_markup=get_hours_keyboard())
        
    if message.text == "✍️ Boshqa":
        await state.set_state(AdminSalaryStates.custom_worked_days)
        return await message.answer("📅 Ishlagan kunni o'zingiz kiriting:", reply_markup=get_manual_keyboard())

    if not message.text.isdigit():
        return await message.answer("❌ Iltimos, to'g'ri kunni tanlang yoki raqam kiriting:")

    await state.update_data(worked_days=int(message.text))
    await state.set_state(AdminSalaryStates.has_ielts)
    await message.answer("🎓 IELTS bormi?", reply_markup=get_yes_no_keyboard())

# 4a. Custom kun kiritilganda -> IELTS so'rash
@start_router.message(AdminSalaryStates.custom_worked_days)
async def process_custom_days(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(AdminSalaryStates.worked_days)
        return await message.answer("📅 Ishlagan kunni tanlang:", reply_markup=get_days_keyboard())

    if not message.text.isdigit():
        return await message.answer("❌ Iltimos, faqat raqam kiriting (Masalan: 26):")

    await state.update_data(worked_days=int(message.text))
    await state.set_state(AdminSalaryStates.has_ielts)
    await message.answer("🎓 IELTS bormi?", reply_markup=get_yes_no_keyboard())

# 5. IELTS -> Rus tili so'rash
@start_router.message(AdminSalaryStates.has_ielts)
async def process_ielts(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(AdminSalaryStates.worked_days)
        return await message.answer("📅 Ishlagan kunni tanlang:", reply_markup=get_days_keyboard())

    await state.update_data(has_ielts=message.text)
    await state.set_state(AdminSalaryStates.knows_russian)
    await message.answer("🇷🇺 Rus tili bormi?", reply_markup=get_yes_no_keyboard())

# 6. Rus tili -> Ish qoldirganini so'rash
@start_router.message(AdminSalaryStates.knows_russian)
async def process_russian(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(AdminSalaryStates.has_ielts)
        return await message.answer("🎓 IELTS bormi?", reply_markup=get_yes_no_keyboard())

    await state.update_data(knows_russian=message.text)
    await state.set_state(AdminSalaryStates.missed)
    await message.answer("📉 Ish qoldirgan kunlaringiz bo'ldimi?", reply_markup=get_yes_no_keyboard())

# 7. Ish qoldirgan kunlar savoli
@start_router.message(AdminSalaryStates.missed)
async def process_missed(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(AdminSalaryStates.knows_russian)
        return await message.answer("🇷🇺 Rus tili bormi?", reply_markup=get_yes_no_keyboard())

    if message.text == "✅ HA":
        await state.set_state(AdminSalaryStates.missed_hours)
        await message.answer("⏰ Necha soat ish qoldirdingiz? (Javobni kiriting):", reply_markup=get_manual_keyboard())
    else:
        await state.update_data(missed_hours=0)
        await state.set_state(AdminSalaryStates.cover)
        await message.answer("🔄 Cover qildingizmi?", reply_markup=get_yes_no_keyboard())

# 7a. Ish qoldirilgan soat kiritilganda -> Cover so'rash
@start_router.message(AdminSalaryStates.missed_hours)
async def process_missed_hours(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(AdminSalaryStates.missed)
        return await message.answer("📉 Ish qoldirgan kunlaringiz bo'ldimi?", reply_markup=get_yes_no_keyboard())

    if not message.text.replace('.', '', 1).isdigit():
        return await message.answer("❌ Iltimos, soatni faqat raqamda kiriting:")

    await state.update_data(missed_hours=float(message.text))
    await state.set_state(AdminSalaryStates.cover)
    await message.answer("🔄 Cover qildingizmi?", reply_markup=get_yes_no_keyboard())

# 8. Cover qildingizmi savoli
@start_router.message(AdminSalaryStates.cover)
async def process_cover(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(AdminSalaryStates.missed)
        return await message.answer("📉 Ish qoldirgan kunlaringiz bo'ldimi?", reply_markup=get_yes_no_keyboard())

    if message.text == "✅ HA":
        await state.set_state(AdminSalaryStates.cover_hours)
        await message.answer("⏰ Nechi soat cover qildingiz? (Javobni kiriting):", reply_markup=get_manual_keyboard())
    else:
        await state.update_data(cover_hours=0)
        await state.set_state(AdminSalaryStates.individual_plan)
        await message.answer("💰 Individual plan kiriting (Faqat raqam):", reply_markup=get_manual_keyboard())

# 8a. Cover soati kiritilganda -> Individual plan so'rash
@start_router.message(AdminSalaryStates.cover_hours)
async def process_cover_hours(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(AdminSalaryStates.cover)
        return await message.answer("🔄 Cover qildingizmi?", reply_markup=get_yes_no_keyboard())

    if not message.text.replace('.', '', 1).isdigit():
        return await message.answer("❌ Iltimos, soatni faqat raqamda kiriting:")

    await state.update_data(cover_hours=float(message.text))
    await state.set_state(AdminSalaryStates.individual_plan)
    await message.answer("💰 Individual plan kiriting (Faqat raqam):", reply_markup=get_manual_keyboard())

# 9. Individual Plan -> Faktik Savdo so'rash
@start_router.message(AdminSalaryStates.individual_plan)
async def process_individual_plan(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(AdminSalaryStates.cover)
        return await message.answer("🔄 Cover qildingizmi?", reply_markup=get_yes_no_keyboard())

    if not message.text.replace('.', '', 1).isdigit():
        return await message.answer("❌ Iltimos, rejani faqat raqamda kiriting:")

    await state.update_data(individual_plan=float(message.text))
    await state.set_state(AdminSalaryStates.actual_sales)
    await message.answer("📊 Actual sales (Faktik savdo) kiriting:", reply_markup=get_manual_keyboard())

# 10. Faktik Savdo -> Konversiya rejasi so'rash
@start_router.message(AdminSalaryStates.actual_sales)
async def process_actual_sales(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(AdminSalaryStates.individual_plan)
        return await message.answer("💰 Individual plan kiriting (Faqat raqam):", reply_markup=get_manual_keyboard())

    if not message.text.replace('.', '', 1).isdigit():
        return await message.answer("❌ Iltimos, faktik savdoni faqat raqamda kiriting:")

    await state.update_data(actual_sales=float(message.text))
    await state.set_state(AdminSalaryStates.conversion_plan)
    await message.answer("📈 Conversion plan (Konversiya rejasi %) kiriting:", reply_markup=get_manual_keyboard())

# 11. Konversiya rejasi -> Faktik konversiya so'rash
@start_router.message(AdminSalaryStates.conversion_plan)
async def process_conversion_plan(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(AdminSalaryStates.actual_sales)
        return await message.answer("📊 Actual sales (Faktik savdo) kiriting:", reply_markup=get_manual_keyboard())

    if not message.text.replace('.', '', 1).isdigit():
        return await message.answer("❌ Iltimos, konversiya rejasini faqat raqamda kiriting:")

    await state.update_data(conversion_plan=float(message.text))
    await state.set_state(AdminSalaryStates.actual_conversion)
    await message.answer("📉 Actual conversion (Faktik konversiya %) kiriting:", reply_markup=get_manual_keyboard())

# 12. Faktik konversiya -> Aktivlar rejasi so'rash
@start_router.message(AdminSalaryStates.actual_conversion)
async def process_actual_conversion(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(AdminSalaryStates.conversion_plan)
        return await message.answer("📈 Conversion plan (Konversiya rejasi %) kiriting:", reply_markup=get_manual_keyboard())

    if not message.text.replace('.', '', 1).isdigit():
        return await message.answer("❌ Iltimos, faktik konversiyani faqat raqamda kiriting:")

    await state.update_data(actual_conversion=float(message.text))
    await state.set_state(AdminSalaryStates.active_plan)
    await message.answer("👥 Active plan (Aktivlar rejasi) kiriting:", reply_markup=get_manual_keyboard())

# 13. Aktivlar rejasi -> Faktik aktivlar so'rash
@start_router.message(AdminSalaryStates.active_plan)
async def process_active_plan(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(AdminSalaryStates.actual_conversion)
        return await message.answer("📉 Actual conversion (Faktik konversiya %) kiriting:", reply_markup=get_manual_keyboard())

    if not message.text.replace('.', '', 1).isdigit():
        return await message.answer("❌ Iltimos, aktivlar rejasini faqat raqamda kiriting:")

    await state.update_data(active_plan=float(message.text))
    await state.set_state(AdminSalaryStates.actual_active)
    await message.answer("👤 Actual active (Faktik aktivlar) kiriting:", reply_markup=get_manual_keyboard())

# 14. Faktik aktivlar -> REAL JAVOBNI HISOBLASH VA CHIQARISH
@start_router.message(AdminSalaryStates.actual_active)
async def process_actual_active_final(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(AdminSalaryStates.active_plan)
        return await message.answer("👥 Active plan (Aktivlar rejasi) kiriting:", reply_markup=get_manual_keyboard())

    if not message.text.replace('.', '', 1).isdigit():
        return await message.answer("❌ Iltimos, faktik aktivlarni faqat raqamda kiriting:")

    await state.update_data(actual_active=float(message.text))
    
    # Barcha ma'lumotlarni yig'ib olamiz
    data = await state.get_data()
    await state.clear()

    # 🧮 Real hisob-kitobni ishga tushiramiz
    result = calculate_admin_salary(data)
    
    # 📝 Chiroyli yakuniy xabar formati
    report_text = (
        f"💰 <b>OYLIK HISOB-KITOB PANELI</b>\n\n"
        f"🧑‍💼 <b>Status:</b> {str(data.get('status')).upper()}\n"
        f"⏰ <b>Ish tartibi:</b> {data.get('daily_hours')} soat / {data.get('worked_days')} kun\n\n"
        f"💵 <b>Fixa maosh:</b> {result['fixa']:,} so'm\n"
        f"🏆 <b>KPI Bonus:</b> {result['final_kpi_bonus']:,} so'm\n\n"
        f"🎁 <b>Qo'shimchalar:</b>\n"
        f"🇷🇺 Rus tili bonus: +{result['russian_bonus']:,} so'm\n"
        f"🎓 IELTS bonus: +{result['ielts_bonus']:,} so'm\n"
        f"🔄 Cover bonus: +{result['cover_bonus']:,} so'm\n\n"
        f"📉 <b>Jarima (Ish qoldirish):</b> -{result['penalty']:,} so'm\n"
        f"📊 <b>Umumiy KPI:</b> {result['weighted_kpi']}%\n"
        f"-----------------------------------------\n"
        f"🏁 <b>JAMI OYLIK MAOSH:</b> <u>{result['total_salary']:,} so'm</u>"
    )
    
    await message.answer(text=report_text, parse_mode="HTML", reply_markup=main_menu_keyboard)

# ==============================================================================
# 💰 KASSIR OYLIK TIZIMI (CASHIER SALARY PROCESS)
# ==============================================================================

# Yordamchi klaviaturalar (Kassir savollari uchun)
def get_cashier_hours_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="6"), types.KeyboardButton(text="7"), types.KeyboardButton(text="8")],
            [types.KeyboardButton(text="✍️ Boshqa")],
            [types.KeyboardButton(text="🏠 Bosh sahifa")]
        ], resize_keyboard=True
    )

def get_cashier_days_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="24"), types.KeyboardButton(text="25"), types.KeyboardButton(text="26")],
            [types.KeyboardButton(text="✍️ Boshqa")],
            [types.KeyboardButton(text="⬅️ Ortga")]
        ], resize_keyboard=True
    )

def get_cashier_yes_no_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="✅ HA"), types.KeyboardButton(text="❌ YO'Q")],
            [types.KeyboardButton(text="⬅️ Ortga")]
        ], resize_keyboard=True
    )

# 1. Kassir oylik tugmasi bosilganda (Tugmadagi matn bilan 100% bir xil qilindi)
@start_router.message(F.text == "💰 Kassir oylik")
async def start_cashier_salary(message: types.Message, state: FSMContext):
    await state.set_state(CashierSalaryStates.hours)
    await message.answer("⏰ Kunlik ish soatini tanlang:", reply_markup=get_cashier_hours_keyboard())

# 2. Ish soati tanlanganda
@start_router.message(CashierSalaryStates.hours)
async def process_cashier_hours(message: types.Message, state: FSMContext):
    if message.text == "🏠 Bosh sahifa":
        await state.clear()
        return await message.answer("Asosiy menyudasiz:", reply_markup=main_menu_keyboard)
    if message.text == "✍️ Boshqa":
        await state.set_state(CashierSalaryStates.custom_hours)
        return await message.answer("⏰ Soatni o'zingiz kiriting:", reply_markup=get_manual_keyboard())
    if not message.text.isdigit():
        return await message.answer("❌ Iltimos, tugmalardan foydalaning yoki raqam kiriting:")

    await state.update_data(hours=int(message.text))
    await state.set_state(CashierSalaryStates.days)
    await message.answer("📅 Ishlagan kunni tanlang:", reply_markup=get_cashier_days_keyboard())

# 3. Custom soat kiritilganda
@start_router.message(CashierSalaryStates.custom_hours)
async def process_cashier_custom_hours(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(CashierSalaryStates.hours)
        return await message.answer("⏰ Kunlik ish soatini tanlang:", reply_markup=get_cashier_hours_keyboard())
    if not message.text.isdigit():
        return await message.answer("❌ Faqat raqam kiriting:")

    await state.update_data(hours=int(message.text))
    await state.set_state(CashierSalaryStates.days)
    await message.answer("📅 Ishlagan kunni tanlang:", reply_markup=get_cashier_days_keyboard())

# 4. Ish kunlari tanlanganda
@start_router.message(CashierSalaryStates.days)
async def process_cashier_days(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(CashierSalaryStates.hours)
        return await message.answer("⏰ Kunlik ish soatini tanlang:", reply_markup=get_cashier_hours_keyboard())
    if message.text == "✍️ Boshqa":
        await state.set_state(CashierSalaryStates.custom_days)
        return await message.answer("📅 Ishlagan kunni o'zingiz kiriting:", reply_markup=get_manual_keyboard())
    if not message.text.isdigit():
        return await message.answer("❌ To'g'ri kun kiriting:")

    await state.update_data(days=int(message.text))
    await state.set_state(CashierSalaryStates.cover)
    await message.answer("🔄 Cover qildingizmi?", reply_markup=get_cashier_yes_no_keyboard())

# 5. Custom kun kiritilganda
@start_router.message(CashierSalaryStates.custom_days)
async def process_cashier_custom_days(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(CashierSalaryStates.days)
        return await message.answer("📅 Ishlagan kunni tanlang:", reply_markup=get_cashier_days_keyboard())
    if not message.text.isdigit():
        return await message.answer("❌ Faqat raqam kiriting:")

    await state.update_data(days=int(message.text))
    await state.set_state(CashierSalaryStates.cover)
    await message.answer("🔄 Cover qildingizmi?", reply_markup=get_cashier_yes_no_keyboard())

# 6. Cover savoli
@start_router.message(CashierSalaryStates.cover)
async def process_cashier_cover(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(CashierSalaryStates.days)
        return await message.answer("📅 Ishlagan kunni tanlang:", reply_markup=get_cashier_days_keyboard())
    if message.text == "✅ HA":
        await state.set_state(CashierSalaryStates.cover_hours)
        await message.answer("⏰ Necha soat cover qildingiz? (Faqat raqam):", reply_markup=get_manual_keyboard())
    else:
        await state.update_data(cover_hours=0.0)
        await state.set_state(CashierSalaryStates.missed)
        await message.answer("📉 Ish qoldirgan kunlaringiz bo'ldimi?", reply_markup=get_cashier_yes_no_keyboard())

# 7. Cover soat kiritilganda
@start_router.message(CashierSalaryStates.cover_hours)
async def process_cashier_cover_hours(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(CashierSalaryStates.cover)
        return await message.answer("🔄 Cover qildingizmi?", reply_markup=get_cashier_yes_no_keyboard())
    if not message.text.replace('.', '', 1).isdigit():
        return await message.answer("❌ Soatni raqamda kiriting:")

    await state.update_data(cover_hours=float(message.text))
    await state.set_state(CashierSalaryStates.missed)
    await message.answer("📉 Ish qoldirgan kunlaringiz bo'ldimi?", reply_markup=get_cashier_yes_no_keyboard())

# 8. Ish qoldirish savoli
@start_router.message(CashierSalaryStates.missed)
async def process_cashier_missed(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(CashierSalaryStates.cover)
        return await message.answer("🔄 Cover qildingizmi?", reply_markup=get_cashier_yes_no_keyboard())
    if message.text == "✅ HA":
        await state.set_state(CashierSalaryStates.missed_hours)
        await message.answer("⏰ Necha soat ish qoldirdingiz? (Faqat raqam):", reply_markup=get_manual_keyboard())
    else:
        await state.update_data(missed_hours=0.0)
        await state.set_state(CashierSalaryStates.active_students)
        await message.answer("👥 Active students (Aktiv talabalar) sonini kiriting:", reply_markup=get_manual_keyboard())

# 9. Ish qoldirilgan soat kiritilganda
@start_router.message(CashierSalaryStates.missed_hours)
async def process_cashier_missed_hours(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(CashierSalaryStates.missed)
        return await message.answer("📉 Ish qoldirgan kunlaringiz bo'ldimi?", reply_markup=get_cashier_yes_no_keyboard())
    if not message.text.replace('.', '', 1).isdigit():
        return await message.answer("❌ Soatni raqamda kiriting:")

    await state.update_data(missed_hours=float(message.text))
    await state.set_state(CashierSalaryStates.active_students)
    await message.answer("👥 Active students (Aktiv talabalar) sonini kiriting:", reply_markup=get_manual_keyboard())

# 10. Aktiv talabalar kiritilganda
@start_router.message(CashierSalaryStates.active_students)
async def process_active_students(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(CashierSalaryStates.missed)
        return await message.answer("📉 Ish qoldirgan kunlaringiz bo'ldimi?", reply_markup=get_cashier_yes_no_keyboard())
    if not message.text.isdigit():
        return await message.answer("❌ Iltimos, faqat butun raqam kiriting:")

    await state.update_data(active_students=int(message.text))
    await state.set_state(CashierSalaryStates.active_debtors)
    await message.answer("💸 Active debtors (Aktiv qarzdorlar) sonini kiriting:", reply_markup=get_manual_keyboard())

# 11. Aktiv qarzdorlar kiritilganda
@start_router.message(CashierSalaryStates.active_debtors)
async def process_active_debtors(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(CashierSalaryStates.active_students)
        return await message.answer("👥 Active students (Aktiv talabalar) sonini kiriting:", reply_markup=get_manual_keyboard())
    if not message.text.isdigit():
        return await message.answer("❌ Iltimos, faqat butun raqam kiriting:")

    await state.update_data(active_debtors=int(message.text))
    await state.set_state(CashierSalaryStates.archive_students)
    await message.answer("🗄 Archive students (Arxiv talabalar) sonini kiriting:", reply_markup=get_manual_keyboard())

# 12. Arxiv talabalar kiritilganda
@start_router.message(CashierSalaryStates.archive_students)
async def process_archive_students(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(CashierSalaryStates.active_debtors)
        return await message.answer("💸 Active debtors (Aktiv qarzdorlar) sonini kiriting:", reply_markup=get_manual_keyboard())
    if not message.text.isdigit():
        return await message.answer("❌ Iltimos, faqat butun raqam kiriting:")

    await state.update_data(archive_students=int(message.text))
    await state.set_state(CashierSalaryStates.archive_debtors)
    await message.answer("📉 Archive debtors (Arxiv qarzdorlar) sonini kiriting:", reply_markup=get_manual_keyboard())

# 13. Yakuniy bosqich: Arxiv qarzdorlar kiritilganda REAL HISOB-KITOB NATIJASI
@start_router.message(CashierSalaryStates.archive_debtors)
async def process_cashier_final(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Ortga":
        await state.set_state(CashierSalaryStates.archive_students)
        return await message.answer("🗄 Archive students (Arxiv talabalar) sonini kiriting:", reply_markup=get_manual_keyboard())
    if not message.text.isdigit():
        return await message.answer("❌ Iltimos, faqat raqam kiriting:")

    await state.update_data(archive_debtors=int(message.text))
    data = await state.get_data()
    await state.clear()

    # 🧮 Hisob-kitobni chaqiramiz
    result = calculate_cashier_salary(data)

    # Natija ko'rsatish shabloni (Chiroyli HTML formatda)
    report_text = (
        f"💰 <b>KASSIR OYLIK HISOB-KITOB PANELI</b>\n\n"
        f"⏰ <b>Ish tartibi:</b> {data.get('hours')} soat / {data.get('days')} kun\n"
        f"📊 <b>Umumiy talabalar:</b> {result['total_students']} ta\n"
        f"💸 <b>Jami qarzdor xodimlar:</b> {result['total_debtors']} ta\n"
        f"📉 <b>Qarzdorlik foizi:</b> {result['debt_percentage']}%\n"
        f"🎯 <b>Natija darajasi:</b> {result['status_text']}\n\n"
        f"💵 <b>Ishbay sof oylik:</b> {result['worked_salary']:,} so'm\n"
        f"🏆 <b>Qarzdorlik karrali bonusi (Multiplier):</b> +{result['kpi_bonus_profit']:,} so'm\n"
        f"🔄 <b>Cover bonus:</b> +{result['cover_bonus']:,} so'm\n"
        f"⚠️ <b>Ish qoldirish jarimasi:</b> -{result['missed_penalty']:,} so'm\n"
        f"-----------------------------------------\n"
        f"🏁 <b>JAMI OYLIK MAOSH:</b> <u>{result['total_salary']:,} so'm</u>"
    )

    await message.answer(text=report_text, parse_mode="HTML", reply_markup=main_menu_keyboard)
