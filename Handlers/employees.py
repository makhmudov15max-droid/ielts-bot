from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from Handlers.states import TaskStates
from Keyboards.main_menu import get_main_menu
from utils.access import check_user_access
from utils.users_db import save_users

employees_router = Router()

# Global o'zgaruvchilar
USERS_ROLES = None
ADMIN_ID = None


def init_employees_handler(users_roles, admin_id):
    """Employees handler uchun global o'zgaruvchilarni o'rnatish"""
    global USERS_ROLES, ADMIN_ID
    USERS_ROLES = users_roles
    ADMIN_ID = admin_id
    # Debug uchun
    print(f"DEBUG: init_employees_handler called, USERS_ROLES type: {type(USERS_ROLES)}, len: {len(USERS_ROLES) if USERS_ROLES else 0}")


# ================= XODIMLAR RO'YXATI =================
@employees_router.message(F.text == "👥 Xodimlar")
async def view_employees_handler(message: types.Message):
    # Debug
    print(f"DEBUG: view_employees_handler called, USERS_ROLES is None: {USERS_ROLES is None}")
    
    if USERS_ROLES is None:
        await message.answer("⚠️ Tizim xatosi: Ma'lumotlar yuklanmagan. Iltimos /start buyrug'ini yuboring.")
        return
    
    if not check_user_access(USERS_ROLES, message.from_user.id):
        return
    
    active_staff = {
        u_id: u_info for u_id, u_info in USERS_ROLES.items() 
        if isinstance(u_info, dict) and u_info.get("name") and u_info.get("role") != "rejected" and u_id != str(ADMIN_ID)
    }
    
    if not active_staff:
        await message.answer(text="📭 Hozircha tizimda birorta ham tasdiqlangan xodim mavjud emas.")
        return
        
    response_text = "👥 <b>Tizimdagi joriy xodimlar roʻyxati:</b>\n\n"
    inline_kb = []
    
    for idx, (u_id, u_info) in enumerate(active_staff.items(), 1):
        response_text += f"{idx}. 👤 <b>{u_info['name']}</b> — 🎖 <i>{u_info['role']}</i>\n"
        inline_kb.append([types.InlineKeyboardButton(text=f"⚙️ {u_info['name']}", callback_data=f"editstaff_{u_id}")])
        
    response_text += "\n<i>Tahrirlash yoki botdan chetlashtirish uchun quyidagi tugmalardan kerakli xodimni tanlang:</i>"
    
    await message.answer(
        text=response_text, 
        parse_mode="HTML", 
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=inline_kb)
    )


# ================= XODIM TAHRIRLASH MENYU =================
@employees_router.callback_query(F.data.startswith("editstaff_"))
async def process_edit_staff_callback(call: types.CallbackQuery, state: FSMContext):
    if USERS_ROLES is None:
        await call.answer("⚠️ Tizim xatosi", show_alert=True)
        return
        
    target_user_id = call.data.split("_")[1]
    staff_info = USERS_ROLES.get(target_user_id)
    
    if not staff_info:
        await call.answer(text="⚠️ Bu xodim tizimdan topilmadi!", show_alert=True)
        return
        
    options_kb = [
        [
            types.InlineKeyboardButton(text="✏️ Ism o'zgartirish", callback_data=f"rename_{target_user_id}"),
            types.InlineKeyboardButton(text="🎖 Lavozimni o'zgartirish", callback_data=f"rolechange_{target_user_id}")
        ],
        [
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


# ================= ISM O'ZGARTIRISH =================
@employees_router.callback_query(F.data.startswith("rename_"))
async def rename_staff_callback(call: types.CallbackQuery, state: FSMContext):
    if USERS_ROLES is None:
        await call.answer("⚠️ Tizim xatosi", show_alert=True)
        return
        
    target_user_id = call.data.split("_")[1]
    staff_info = USERS_ROLES.get(target_user_id)
    
    if not staff_info:
        await call.answer(text="⚠️ Xodim topilmadi!", show_alert=True)
        return
    
    await state.update_data(rename_user_id=target_user_id)
    await state.set_state(TaskStates.waiting_for_new_name)
    
    await call.message.answer(
        text=f"✏️ <b>{staff_info['name']}</b> uchun yangi ism va familiyani kiriting:",
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await call.answer()


@employees_router.message(TaskStates.waiting_for_new_name)
async def process_new_name_handler(message: types.Message, state: FSMContext):
    if USERS_ROLES is None:
        await message.answer("⚠️ Tizim xatosi. Iltimos /start buyrug'ini yuboring.")
        await state.clear()
        return
        
    user_data = await state.get_data()
    target_user_id = user_data.get("rename_user_id")
    new_name = message.text.strip()
    
    if target_user_id and target_user_id in USERS_ROLES:
        old_name = USERS_ROLES[target_user_id]["name"]
        USERS_ROLES[target_user_id]["name"] = new_name
        await save_users(USERS_ROLES)
        
        await message.answer(
            text=f"✅ <b>Ism muvaffaqiyatli o‘zgartirildi!</b>\n\n"
                 f"📝 Eski ism: {old_name}\n"
                 f"📝 Yangi ism: {new_name}",
            parse_mode="HTML"
        )
        
        try:
            await message.bot.send_message(
                chat_id=int(target_user_id),
                text=f"🔔 Administrator tomonidan sizning ismingiz <b>{new_name}</b> ga o‘zgartirildi.",
                parse_mode="HTML"
            )
        except:
            pass
        
        role = USERS_ROLES[str(message.from_user.id)]["role"]
        await message.answer(
            text="Xodimlar paneliga qaytdingiz.",
            reply_markup=get_main_menu(role)
        )
    
    await state.clear()


# ================= LAVOZIMNI O'ZGARTIRISH =================
@employees_router.callback_query(F.data.startswith("rolechange_"))
async def process_role_change_menu(call: types.CallbackQuery):
    if USERS_ROLES is None:
        await call.answer("⚠️ Tizim xatosi", show_alert=True)
        return
        
    target_user_id = call.data.split("_")[1]
    
    roles = ["Admin", "Kassir", "Sanitar", "Manager", "Maintenance", "Head Admin"]
    inline_kb = []
    row = []
    
    for r in roles:
        row.append(types.InlineKeyboardButton(text=r, callback_data=f"setnewrole_{r}_{target_user_id}"))
        if len(row) == 2:
            inline_kb.append(row)
            row = []
    if row:  # Qolgan tugmalar (juft bo'lmasa)
        inline_kb.append(row)
            
    inline_kb.append([types.InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"editstaff_{target_user_id}")])
    
    await call.message.edit_text(
        text="⚙️ Xodim uchun <b>yangi lavozimni</b> tanlang:",
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=inline_kb)
    )
    await call.answer()


@employees_router.callback_query(F.data.startswith("setnewrole_"))
async def save_new_role_callback(call: types.CallbackQuery, state: FSMContext):
    if USERS_ROLES is None:
        await call.answer("⚠️ Tizim xatosi", show_alert=True)
        return
        
    data_parts = call.data.split("_")
    new_role = data_parts[1]
    target_user_id = data_parts[2]
    
    if target_user_id in USERS_ROLES:
        USERS_ROLES[target_user_id]["role"] = new_role
        await save_users(USERS_ROLES)
        staff_name = USERS_ROLES[target_user_id]["name"]
        
        await call.message.edit_text(
            text=f"✅ <b>Muvaffaqiyatli oʻzgartirildi!</b>\n\n"
                 f"👤 Xodim: <b>{staff_name}</b>\n"
                 f"🎖 Yangi lavozimi: <b>{new_role}</b>",
            parse_mode="HTML"
        )
        
        try:
            await call.bot.send_message(
                chat_id=int(target_user_id),
                text=f"🔔 <b>Diqqat!</b> Administrator tomonidan sizning lavozimingiz <b>{new_role}</b> etib belgilandi.",
                parse_mode="HTML",
                reply_markup=get_main_menu(new_role)
            )
        except Exception as e:
            print(f"Xodimni rolda ogohlantirishda xatolik: {e}")
    else:
        await call.answer(text="⚠️ Xatolik: Xodim topilmadi!", show_alert=True)
        
    await state.clear()
    await call.answer()


# ================= XODIMNI CHETLATIRISH =================
@employees_router.callback_query(F.data.startswith("firestaff_"))
async def fire_staff_callback(call: types.CallbackQuery, state: FSMContext):
    if USERS_ROLES is None:
        await call.answer("⚠️ Tizim xatosi", show_alert=True)
        return
        
    target_user_id = call.data.split("_")[1]
    
    if target_user_id in USERS_ROLES:
        staff_name = USERS_ROLES[target_user_id]["name"]
        USERS_ROLES[target_user_id]["role"] = "rejected"
        await save_users(USERS_ROLES)
        
        await call.message.edit_text(
            text=f"❌ <b>Xodim botdan chetlashtirildi!</b>\n\n"
                 f"👤 <b>{staff_name}</b> endi tizimga kira olmaydi va unga avtomatik vazifalar yuborilmaydi.",
            parse_mode="HTML"
        )
        
        try:
            await call.bot.send_message(
                chat_id=int(target_user_id),
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


@employees_router.callback_query(F.data == "editstaff_cancel")
async def cancel_edit_staff_callback(call: types.CallbackQuery, state: FSMContext):
    if USERS_ROLES is None:
        await call.answer("⚠️ Tizim xatosi", show_alert=True)
        return
    await call.message.delete()
    role = USERS_ROLES[str(call.from_user.id)]["role"]
    await call.message.answer(text="Xodimlarni boshqarish paneli yopildi.", reply_markup=get_main_menu(role))
    await state.clear()
    await call.answer()


# ================= ARXIV =================
@employees_router.message(F.text == "🗄 Arxiv")
async def view_archive_handler(message: types.Message):
    if USERS_ROLES is None:
        await message.answer("⚠️ Tizim xatosi. Iltimos /start buyrug'ini yuboring.")
        return
        
    if not check_user_access(USERS_ROLES, message.from_user.id):
        return
    
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
        display_name = u_info.get("name") if u_info.get("name") else f"Foydalanuvchi [ID: {u_id}]"
        response_text += f"{idx}. ❌ <b>{display_name}</b> — <i>Tizimdan chetlashtirilgan</i>\n"
        inline_kb.append([types.InlineKeyboardButton(text=f"🔄 {display_name}", callback_data=f"restorestaff_{u_id}")])
        
    response_text += "\n<i>Ushbu foydalanuvchilarni qayta faollashtirish va lavozim berish uchun mos tugmani bosing:</i>"
    
    await message.answer(
        text=response_text,
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=inline_kb)
    )


@employees_router.callback_query(F.data.startswith("restorestaff_"))
async def process_restore_staff_callback(call: types.CallbackQuery):
    if USERS_ROLES is None:
        await call.answer("⚠️ Tizim xatosi", show_alert=True)
        return
        
    target_user_id = call.data.split("_")[1]
    user_info = USERS_ROLES.get(target_user_id)
    
    if not user_info:
        await call.answer(text="⚠️ Bu foydalanuvchi ma'lumotlar bazasidan topilmadi!", show_alert=True)
        return
        
    display_name = user_info.get("name") if user_info.get("name") else f"Foydalanuvchi [{target_user_id}]"
    
    roles = ["Admin", "Kassir", "Sanitar", "Manager", "Maintenance", "Head Admin"]
    inline_kb = []
    row = []
    
    for r in roles:
        row.append(types.InlineKeyboardButton(text=r, callback_data=f"savearchiverole_{r}_{target_user_id}"))
        if len(row) == 2:
            inline_kb.append(row)
            row = []
    if row:  # Qolgan tugmalar
        inline_kb.append(row)
            
    inline_kb.append([types.InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="editstaff_cancel")])
    
    await call.message.edit_text(
        text=f"🔄 <b>Foydalanuvchi:</b> {display_name}\n\n"
             f"Ushbu xodimni faollashtirish uchun <b>yangi lavozimni (rol)</b> tanlang:",
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=inline_kb)
    )
    await call.answer()


@employees_router.callback_query(F.data.startswith("savearchiverole_"))
async def save_archive_role_callback(call: types.CallbackQuery, state: FSMContext):
    if USERS_ROLES is None:
        await call.answer("⚠️ Tizim xatosi", show_alert=True)
        return
        
    data_parts = call.data.split("_")
    new_role = data_parts[1]
    target_user_id = data_parts[2]
    
    if target_user_id in USERS_ROLES:
        USERS_ROLES[target_user_id]["role"] = new_role
        await save_users(USERS_ROLES)
        
        has_name = USERS_ROLES[target_user_id].get("name") is not None
        display_name = USERS_ROLES[target_user_id]["name"] if has_name else "Xodim"
        
        await call.message.edit_text(
            text=f"✅ <b>Muvaffaqiyatli tiklandi!</b>\n\n"
                 f"👤 Xodim: <b>{display_name}</b>\n"
                 f"🎖 Yangi biriktirilgan lavozim: <b>{new_role}</b>\n\n"
                 f"<i>Xodimga tizim qayta faollashtirilgani haqida xabarnoma yuborildi.</i>",
            parse_mode="HTML"
        )
        
        try:
            if has_name:
                await call.bot.send_message(
                    chat_id=int(target_user_id),
                    text=f"🎉 <b>Xushxabar!</b> Administrator sizni arxivdan chiqardi va joriy lavozimingizni <b>{new_role}</b> etib belgiladi.\n"
                         f"Bot imkoniyatlaridan toʻliq foydalanishingiz mumkin!",
                    parse_mode="HTML",
                    reply_markup=get_main_menu(new_role)
                )
            else:
                await call.bot.send_message(
                    chat_id=int(target_user_id),
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
