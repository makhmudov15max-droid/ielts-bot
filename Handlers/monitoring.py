from utils.attendance_db import (
    add_attendance,
    get_attendance_by_user_and_month,
    get_attendance_by_user_today,
    get_attendance_by_dates,
    has_checkin_today,
    get_missed_days,
)
from utils.users_db import get_user_work_time, get_motivation_index, increment_motivation_index
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta, timezone
import calendar
import logging

from Keyboards.main_menu import get_main_menu, get_back_home_keyboard
# ================= 200 MOTIVATSION XABARLAR =================
MOTIVATION_MESSAGES = [
    "✅ Ajoyib! Ish kunini intizom bilan boshladingiz.",
    "🌟 Vaqtida kelish — muvaffaqiyatning birinchi qadami.",
    "🚀 Bugun ham o\'zingizga bergan va\'dangizni bajardingiz.",
    "💪 Intizomli insonlar katta natijalarga erishadi.",
    "🎯 Maqsad sari yana bir qadam tashlandi.",
    "🔥 Zo\'r! Kuningizni kuchli boshladingiz.",
    "⭐ Davomat tasdiqlandi. Rahmat!",
    "👏 Mas\'uliyatli yondashuvingiz tahsinga loyiq.",
    "🌱 Kichik odatlar katta muvaffaqiyatlarni yaratadi.",
    "🏆 Bugungi kun uchun yaxshi start!",
    "⚡ Vaqtni qadrlash — o\'zingizni qadrlashdir.",
    "🌞 Kuningiz barakali o\'tsin!",
    "💼 Professional yondashuvingiz uchun rahmat.",
    "🎉 Yana bir intizomli kun boshlandi.",
    "🚩 Siz to\'g\'ri yo\'ldasiz.",
    "🌈 Har bir vaqtida kelish — yangi imkoniyat.",
    "🥇 Intizom sizning kuchli tomonlaringizdan biri.",
    "📈 Muvaffaqiyat har kuni takrorlanadigan odatlardan boshlanadi.",
    "🔔 Davomat muvaffaqiyatli qayd etildi.",
    "💎 Sizning intizomingiz qadrli.",
    "🚀 Ish kuningiz samarali o\'tsin!",
    "🌟 Zo\'r natijalar intizomdan boshlanadi.",
    "👌 Bugungi kunni mukammal boshladingiz.",
    "🔥 Davom eting, sizda yaxshi ketmoqda.",
    "🎯 Har kuni bir qadam oldinga.",
    "⭐ Bugungi intizomingiz ertangi muvaffaqiyatingizdir.",
    "💪 Siz bunga qodirsiz.",
    "🌞 Yaxshi kayfiyat va yaxshi natijalar tilaymiz.",
    "📊 Kichik yutuqlar katta natijalarga olib keladi.",
    "🏅 Tabriklaymiz! Davomat tasdiqlandi.",
    "🚀 Ishga vaqtida kelganingiz uchun rahmat.",
    "🌱 Bugungi intizom ertangi imkoniyatdir.",
    "🎉 Kuningiz yaxshi boshlanganidan xursandmiz.",
    "⭐ Siz jamoa uchun yaxshi namunasiz.",
    "💼 Professionalizm shunday boshlanadi.",
    "🔥 Intizomni saqlab qoling.",
    "🎯 Harakatda davom eting.",
    "🏆 Sizning mehnatingiz albatta samara beradi.",
    "🌟 Ajoyib odatlarni shakllantiryapsiz.",
    "⚡ Bugungi energiyangiz yuqori bo\'lsin!",
    "💪 Kuchli insonlar vaqtni qadrlaydi.",
    "📈 Yuksalish intizomdan boshlanadi.",
    "🌞 Kuningiz unumli o\'tsin.",
    "🎉 Zo\'r! Siz bugun ham o\'z vaqtidasiz.",
    "🚩 Bu yaxshi odatni davom ettiring.",
    "🥇 Intizomli hodim — muvaffaqiyatli hodim.",
    "⭐ Yana bir yaxshi ish bajarildi.",
    "🔥 O\'zingizni ortda qoldirishda davom eting.",
    "🎯 Maqsadlaringizga yaqinlashyapsiz.",
    "💎 Intizomingiz e\'tiborga loyiq.",
    "🚀 Zo\'r boshlanish — zo\'r natija.",
    "🌱 Har kuni o\'sishda davom eting.",
    "👏 Sizning mas\'uliyatingiz tahsinga sazovor.",
    "⭐ Davomat muvaffaqiyatli qayd qilindi.",
    "💪 Ishonchli odatlar muvaffaqiyat yaratadi.",
    "🔥 Ajoyib! Davom eting.",
    "🎯 Katta natijalar kichik qadamlardan boshlanadi.",
    "🏆 Siz bilan faxrlanamiz.",
    "🌟 Bugungi kun uchun kuchli start.",
    "⚡ Harakatdan to\'xtamang.",
    "💼 Ish kuningizga omad!",
    "🌞 Bugungi kun sizniki.",
    "📈 Har kuni yaxshiroq bo\'lib boryapsiz.",
    "🎉 Intizom uchun rahmat.",
    "⭐ Zo\'r! Bugun ham vaqtidasiz.",
    "🚀 Harakatda baraka bor.",
    "💪 Sizning mehnatingiz qadrlanadi.",
    "🔥 Kuchli odatlar shakllanmoqda.",
    "🎯 Davom eting, natijalar yaqin.",
    "🏅 Bugungi yutug\'ingiz bilan tabriklaymiz.",
    "🌟 Intizom — muvaffaqiyatning kaliti.",
    "💎 Sizning harakatingiz muhim.",
    "🚩 To\'g\'ri yo\'nalishda davom eting.",
    "🌱 O\'sish har kuni boshlanadi.",
    "⚡ Bugungi kuningiz samarali bo\'lsin.",
    "🎉 Zo\'r! Yana bir vaqtida kelish.",
    "📊 Natijalar odatlardan boshlanadi.",
    "💪 Sizning qat\'iyatingiz tahsinga loyiq.",
    "⭐ Ishga mas\'uliyatli yondashuvingiz uchun rahmat.",
    "🔥 Siz kuchli tempdasiz.",
    "🚀 Kuningizni muvaffaqiyat bilan boshladingiz.",
    "🌞 Bugun ham ajoyib imkoniyatlar kutmoqda.",
    "🎯 Maqsad sari dadil qadam.",
    "🏆 Intizomli insonlar doim yutadi.",
    "💎 Zo\'r ish!",
    "🌟 Har bir kun yangi imkoniyat.",
    "💪 O\'zingizning eng yaxshi versiyangizga yaqinlashyapsiz.",
    "🔥 Tempni tushirmang.",
    "📈 Muvaffaqiyat sari harakat davom etmoqda.",
    "⭐ Bugungi kun uchun rahmat!",
    "🚀 Kuningiz omadli o\'tsin.",
    "🌱 Bugungi intizom ertangi natijadir.",
    "🎉 Ajoyib! Siz bugun ham o\'z vaqtidasiz.",
    "💪 Harakatlaringiz besamar ketmaydi.",
    "🎯 Oldinga intilishda davom eting.",
    "🏅 Siz jamoamizning muhim qismisiz.",
    "🌟 Yaxshi odatlar katta yutuqlar olib keladi.",
    "⚡ Zo\'r boshlanish — yarim g\'alaba.",
    "🔥 Davomat tasdiqlandi. Omad tilaymiz!",
    "🏆 Tabriklaymiz! Bugungi kunni ham intizom bilan boshladingiz.",
    "🌅 Erta boshlangan kun ko\'pincha yaxshi natija bilan tugaydi.",
    "✨ Bugungi intizomingiz kelajakdagi muvaffaqiyatingizga sarmoyadir.",
    "🚶 Har kuni oldinga yurayotgan inson albatta manzilga yetadi.",
    "🌿 Barqarorlik sizning kuchli jihatingizga aylanmoqda.",
    "🔑 Natijalar eshigini intizom ochadi.",
    "📌 Vaqtida yetib kelish — mas\'uliyat belgisi.",
    "🌠 Kuningizni to\'g\'ri boshlab oldingiz.",
    "🧭 To\'g\'ri odatlar to\'g\'ri natijalarga olib boradi.",
    "🛡️ Ishonchlilik eng qimmat fazilatlardan biridir.",
    "🎈 Bugungi kun uchun birinchi vazifa muvaffaqiyatli bajarildi.",
    "🌄 Ertalabki g\'alabalar kun bo\'yi kuch beradi.",
    "🚦 Siz bugungi kunni yashil chiroq bilan boshladingiz.",
    "🌻 Intizom mehnatni qadrlashdan boshlanadi.",
    "🏹 Nishonga yaqinlashishda davom etyapsiz.",
    "🪜 Muvaffaqiyat zinapoyasining yana bir pog\'onasiga chiqdingiz.",
    "📚 Har bir yaxshi odat kelajakdagi ustunlikdir.",
    "🌊 Barqaror harakat katta to\'lqinlarni hosil qiladi.",
    "🔆 Sizning bugungi qaroringiz to\'g\'ri bo\'ldi.",
    "🎖️ Intizom doimo e\'tibordan chetda qolmaydi.",
    "🚴 Tez emas, ammo to\'xtamasdan harakat qilish muhim.",
    "🌍 Katta o\'zgarishlar kichik qadamlardan boshlanadi.",
    "🎇 Yangi kun, yangi imkoniyatlar.",
    "🔋 Kuningiz energiyaga boy bo\'lsin.",
    "📍 Bugungi kun uchun pozitsiyangiz mustahkam.",
    "🌳 Har kuni ildiz otayotgan daraxt kabi rivojlanyapsiz.",
    "🎊 O\'zingizga qo\'ygan talablaringizni oqladingiz.",
    "🧱 Muvaffaqiyat poydevoriga yana bir g\'isht qo\'shildi.",
    "🌸 Intizomli insonlarga omad ham ko\'proq kulib boqadi.",
    "🛰️ Kursdan chiqmayotganingiz tahsinga loyiq.",
    "⏰ Vaqtni hurmat qilganingiz uchun rahmat.",
    "🚪 Imkoniyatlar odatda tayyor insonlarga ochiladi.",
    "🏔️ Cho\'qqilar sabr va intizom bilan zabt etiladi.",
    "🔭 Maqsadingiz sari yo\'nalish to\'g\'ri.",
    "🧩 Jamoa muvaffaqiyatining bir bo\'lagi sizsiz.",
    "🌤️ Kuningiz yorug\' va samarali o\'tsin.",
    "🏵️ Siz yaxshi odatlarni mustahkamlayapsiz.",
    "🚢 To\'g\'ri yo\'nalishda suzayotgan kema manzilga yetadi.",
    "🌟 Bugun ham namuna bo\'la oldingiz.",
    "🪙 Har bir intizomli kun qimmatli tajriba.",
    "📣 Bugungi bosqich muvaffaqiyatli yakunlandi.",
    "🎋 O\'sish davom etmoqda.",
    "🧠 Kuchli natijalar kuchli odatlardan tug\'iladi.",
    "🌞 Ish kuni siz uchun yaxshi imkoniyatlar olib kelsin.",
    "🏗️ Kelajagingizni bugundan qurmoqdasiz.",
    "🚄 Tezlikdan ham muhimroq narsa — izchillik.",
    "🎯 Yo\'nalishingiz aniq, davom eting.",
    "🔔 Yaxshi odatlar yana bir bor o\'zini ko\'rsatdi.",
    "🌌 Kichik g\'alabalarni qadrlashni unutmang.",
    "📈 Rivojlanish yo\'lidasiz.",
    "🎁 Bugungi intizom ertangi mukofotdir.",
    "🪄 Natijalar mo\'jiza emas, odatlar mahsuli.",
    "🚀 Boshlanish ajoyib bo\'ldi.",
    "🌾 Mehnat urug\'lari vaqt bilan hosil beradi.",
    "🧭 Yo\'nalishni saqlab qoling.",
    "🎪 Har bir kun o\'z imkoniyatiga ega.",
    "📖 Yaxshi hikoyalar yaxshi odatlardan boshlanadi.",
    "🔥 Bugungi harakatingiz ertaga foyda beradi.",
    "🏹 Siz maqsadga yaqinlashmoqdasiz.",
    "🌼 Intizom — o\'zingizga hurmat ko\'rsatishdir.",
    "🚩 Kuningiz yaxshi boshlandi.",
    "🌈 Har bir yangi tong yangi imkoniyatdir.",
    "🏆 Barqarorlikning o\'zi katta yutuq.",
    "🎡 Harakatda davom etgan inson oldinga chiqadi.",
    "🗺️ Rejaga sodiqlik kuchli fazilat.",
    "🌍 Sizning hissangiz muhim.",
    "🔋 Bugungi kun uchun zaryad olindi.",
    "🧱 Natijalaringiz qurilmoqda.",
    "🌟 Bir kun emas, har kuni muhim.",
    "🎯 E\'tiboringiz va mas\'uliyatingiz uchun rahmat.",
    "🚴 Oldinga harakat davom etmoqda.",
    "🌺 Intizom gullari keyinroq hosil beradi.",
    "📊 Kuchli tizim kuchli natija beradi.",
    "🚀 Bugungi kunning birinchi yutug\'i qo\'lga kiritildi.",
    "🛤️ Yo\'ldan chiqmayotganingiz tahsinga loyiq.",
    "🌄 Ertalabki g\'alaba kunni bezaydi.",
    "🧠 Har bir yaxshi odat kelajakni o\'zgartiradi.",
    "🔑 Siz kalit odatlarni shakllantiryapsiz.",
    "🌱 Har kuni oz bo\'lsa ham o\'sish muhim.",
    "📍 Belgilangan nuqtaga vaqtida yetdingiz.",
    "🎉 Yaxshi boshlanish!",
    "🏔️ Cho\'qqi sari qadamlar davom etmoqda.",
    "🌞 Bugun ham ishonchli inson ekaningizni ko\'rsatdingiz.",
    "🎗️ Intizom sizni ajratib turadi.",
    "📈 Natijalar yig\'ilib bormoqda.",
    "🌻 Kuningiz samarali kechsin.",
    "🚦 Reja bo\'yicha harakat davom etmoqda.",
    "🏹 Nishondan ko\'zingizni uzmang.",
    "🌊 Izchil harakat kuch beradi.",
    "🎖️ Mas\'uliyat e\'tirofga loyiq.",
    "🧩 Katta rasmning muhim bo\'lagisiz.",
    "🔆 Kuningiz yorqin bo\'lsin.",
    "📚 Tajriba va odatlar yig\'ilmoqda.",
    "🚪 Yangi imkoniyatlar sizni kutmoqda.",
    "🏅 Ishonchlilik — katta boylik.",
    "🌳 Har kuni kuchayib boryapsiz.",
    "🎯 Maqsad sari temp yaxshi.",
    "🚀 Sizning ritmingiz yaxshi.",
    "🌟 Intizom yo\'qolmaydigan investitsiya.",
    "📌 Kuningiz muvaffaqiyatli boshlandi.",
    "🛡️ Sizga ishonish mumkin.",
]


from utils.access import check_user_access
from utils.holidays_db import is_today_global_holiday, get_all_holidays

monitoring_router = Router()

TASHKENT_TZ = timezone(timedelta(hours=5))

# ================= GLOBAL O'ZGARUVCHILAR =================
USERS_ROLES = None


def init_monitoring_handler(users_roles):
    global USERS_ROLES
    USERS_ROLES = users_roles


# ================= STATES =================
class MonitoringStates(StatesGroup):
    waiting_for_late_time = State()
    waiting_for_late_reason = State()
    waiting_for_late_proof = State()
    waiting_for_role = State()
    waiting_for_employee_choice = State()
    waiting_for_period = State()
    waiting_for_custom_dates = State()


# ================= KEYBOARDS =================
def get_role_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Admin"), types.KeyboardButton(text="Kassir")],
            [types.KeyboardButton(text="Sanitar"), types.KeyboardButton(text="Manager")],
            [types.KeyboardButton(text="Maintenance")],
            [types.KeyboardButton(text="🏠 Bosh sahifa"), types.KeyboardButton(text="⬅️ Ortga")],
        ],
        resize_keyboard=True
    )


def get_employee_list_keyboard(role: str):
    keyboard = []
    employees = []
    
    for u_id, u_info in USERS_ROLES.items():
        if isinstance(u_info, dict) and u_info.get("role") == role and u_info.get("name"):
            employees.append((u_id, u_info["name"]))
    
    if not employees:
        return None
    
    keyboard.append([types.KeyboardButton(text="👥 Barcha xodimlar")])
    for u_id, name in employees:
        keyboard.append([types.KeyboardButton(text=f"👤 {name}")])
    
    keyboard.append([types.KeyboardButton(text="🏠 Bosh sahifa"), types.KeyboardButton(text="⬅️ Ortga")])
    return types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_period_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="📅 Bugun"), types.KeyboardButton(text="📅 Bu oy")], 
            [types.KeyboardButton(text="📆 Sana (multiple select)"), types.KeyboardButton(text="🏠 Bosh sahifa")],
            [types.KeyboardButton(text="⬅️ Ortga")],
        ],
        resize_keyboard=True
    )


def get_late_proof_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="📸 Rasm yuborish"), types.KeyboardButton(text="📹 Video yuborish")],
            [types.KeyboardButton(text="✍️ Isbostsiz davom etish"), types.KeyboardButton(text="🏠 Bosh sahifa")],
            [types.KeyboardButton(text="⬅️ Ortga")],
        ],
        resize_keyboard=True
    )


# ================= BAYRAM KUNLARI UCHUN YORDAMCHI FUNKSIYALAR =================
async def get_holiday_dates() -> set:
    """Barcha ta'til sanalarini (YYYY-MM-DD va MM-DD formatlarida) qaytaradi"""
    holidays = await get_all_holidays()
    holiday_set = set()
    for h in holidays:
        date = h["date"]
        is_repeat = h.get("is_repeat", False)
        if is_repeat:
            holiday_set.add(date)  # MM-DD
        else:
            holiday_set.add(date)  # YYYY-MM-DD
    return holiday_set


def is_holiday_date(date_str: str, holidays_set: set) -> bool:
    """Berilgan sana bayram kunimi tekshiradi"""
    if date_str in holidays_set:
        return True
    mm_dd = date_str[5:]  # "YYYY-MM-DD" dan "MM-DD" ni olish
    return mm_dd in holidays_set


async def format_attendance_report(records: list, title: str) -> str:
    """Attendance report - bayram kunlarini hisobga olgan holda"""
    if not records:
        return f"{title}\n\n📭 Bu davr uchun ma'lumotlar topilmadi."
    
    holidays_set = await get_holiday_dates()
    
    checked_in_days = []
    missed_days = []
    holiday_days = []
    
    for r in records:
        date = r.get("date", "Noma'lum")
        status = r.get("status", "pending")
        arrived_at = r.get("arrived_at", "Noma'lum")
        late_min = r.get("late_minutes", 0)
        reason = r.get("reason", "")
        
        is_holiday = is_holiday_date(date, holidays_set) if holidays_set else False
        
        if status == "checked_in":
            if is_holiday:
                holiday_days.append(f"   {date} - 🎉 BAYRAM (ishga kelgan)")
            elif late_min > 0:
                if reason:
                    checked_in_days.append(f"   {date} - {arrived_at} ({late_min} daqiqa kech) - {reason}")
                else:
                    checked_in_days.append(f"   {date} - {arrived_at} ({late_min} daqiqa kech)")
            else:
                checked_in_days.append(f"   {date} - {arrived_at} (vaqtida)")
        elif status in ["missed", "pending"]:
            if is_holiday:
                holiday_days.append(f"   {date} - 🎉 BAYRAM (dam olish kuni)")
            else:
                missed_days.append(f"   {date} - ❌ Tasdiqlanmagan")
    
    text = f"{title}\n\n"
    
    if holiday_days:
        text += "🎉 <b>Bayram kunlari (ish kuni hisoblanmaydi):</b>\n"
        text += "\n".join(holiday_days) + "\n\n"
    
    if checked_in_days:
        text += "✅ <b>Ishga kelgan kunlar:</b>\n"
        text += "\n".join(checked_in_days) + "\n\n"
    else:
        text += "✅ <b>Ishga kelgan kunlar:</b> Yo'q\n\n"
    
    if missed_days:
        text += "⚠️ <b>Ishga kelmagan / tasdiqlamagan kunlar:</b>\n"
        text += "\n".join(missed_days) + "\n\n"
    
    # Statistikaga bayram kunlarini kiritma (faqat ish kunlari)
    total_work_days = len(checked_in_days)
    total_days_in_period = len(set(r.get("date") for r in records if not is_holiday_date(r.get("date"), holidays_set)))
    
    text += "📊 <b>Statistika (bayramlar hisobga olinmagan):</b>\n"
    text += f"   ✅ Ishlagan kunlar: {total_work_days}/{total_days_in_period}"
    
    return text


def get_all_days_in_current_month():
    now = datetime.now(TASHKENT_TZ)
    _, last_day = calendar.monthrange(now.year, now.month)
    dates = []
    for d in range(1, last_day + 1):
        dates.append(f"{now.year}-{now.month:02d}-{d:02d}")
    return dates


# ================= HELPERS =================
def get_user_id_by_name(name: str):
    clean = name.replace("👤 ", "").strip()
    for u_id, u_info in USERS_ROLES.items():
        if isinstance(u_info, dict) and u_info.get("name") == clean:
            return u_id
    return None


def get_all_users_by_role(role: str):
    users = []
    for u_id, u_info in USERS_ROLES.items():
        if isinstance(u_info, dict) and u_info.get("role") == role and u_info.get("name"):
            users.append((u_id, u_info["name"]))
    return users


# ================= MONITORING ASOSIY MENU =================
@monitoring_router.message(F.text == "🎯 Monitoring")
async def monitoring_main_handler(message: types.Message, state: FSMContext):
    if not check_user_access(USERS_ROLES, message.from_user.id):
        return
    await state.clear()
    await state.set_state(MonitoringStates.waiting_for_role)
    await message.answer(
        text="🎯 <b>Monitoring</b>\n\nQaysi bo'lim xodimlarini ko'rmoqchisiz?",
        parse_mode="HTML",
        reply_markup=get_role_keyboard()
    )


@monitoring_router.message(MonitoringStates.waiting_for_role, F.text == "🏠 Bosh sahifa")
async def monitoring_role_home(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@monitoring_router.message(MonitoringStates.waiting_for_role, F.text == "⬅️ Ortga")
async def monitoring_role_back(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@monitoring_router.message(MonitoringStates.waiting_for_role, F.text.in_(["Admin", "Kassir", "Sanitar", "Manager", "Maintenance"]))
async def monitoring_role_selected(message: types.Message, state: FSMContext):
    role = message.text
    employees = get_all_users_by_role(role)
    
    if not employees:
        await message.answer(f"📭 Tizimda {role} rolidagi xodimlar topilmadi.", reply_markup=get_role_keyboard())
        return
    
    await state.update_data(selected_role=role)
    await state.set_state(MonitoringStates.waiting_for_employee_choice)
    
    keyboard = get_employee_list_keyboard(role)
    await message.answer(
        text=f"👤 <b>{role}lardan birini tanlang:</b>",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@monitoring_router.message(MonitoringStates.waiting_for_role)
async def invalid_role_selected(message: types.Message):
    await message.answer("❌ Iltimos, tugmalardan birini tanlang!", reply_markup=get_role_keyboard())


# ================= XODIM TANLASH =================
@monitoring_router.message(MonitoringStates.waiting_for_employee_choice, F.text == "🏠 Bosh sahifa")
async def monitoring_employee_home(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@monitoring_router.message(MonitoringStates.waiting_for_employee_choice, F.text == "⬅️ Ortga")
async def monitoring_employee_back(message: types.Message, state: FSMContext):
    await state.set_state(MonitoringStates.waiting_for_role)
    await message.answer("Qaysi bo'lim xodimlarini ko'rmoqchisiz?", reply_markup=get_role_keyboard())


@monitoring_router.message(MonitoringStates.waiting_for_employee_choice, F.text == "👥 Barcha xodimlar")
async def monitoring_all_employees_selected(message: types.Message, state: FSMContext):
    data = await state.get_data()
    role = data.get("selected_role")
    await state.update_data(selected_user_id="ALL", selected_name=f"Barcha {role}lar")
    await state.set_state(MonitoringStates.waiting_for_period)
    await message.answer(
        text="📅 <b>Qaysi davr uchun hisobot ko'rmoqchisiz?</b>",
        parse_mode="HTML",
        reply_markup=get_period_keyboard()
    )


@monitoring_router.message(MonitoringStates.waiting_for_employee_choice, F.text.startswith("👤 "))
async def monitoring_employee_selected(message: types.Message, state: FSMContext):
    text = message.text.strip()
    uid = get_user_id_by_name(text)
    
    if not uid:
        data = await state.get_data()
        role = data.get("selected_role", "Admin")
        await message.answer("❌ Xodim topilmadi.", reply_markup=get_employee_list_keyboard(role))
        return
    
    name = text.replace("👤 ", "").strip()
    await state.update_data(selected_user_id=uid, selected_name=name)
    await state.set_state(MonitoringStates.waiting_for_period)
    await message.answer(
        text="📅 <b>Qaysi davr uchun hisobot ko'rmoqchisiz?</b>",
        parse_mode="HTML",
        reply_markup=get_period_keyboard()
    )


@monitoring_router.message(MonitoringStates.waiting_for_employee_choice)
async def invalid_employee_selected(message: types.Message, state: FSMContext):
    data = await state.get_data()
    role = data.get("selected_role", "Admin")
    await message.answer("❌ Iltimos, ro'yxatdan tanlang!", reply_markup=get_employee_list_keyboard(role))


# ================= DAVR TANLASH =================
@monitoring_router.message(MonitoringStates.waiting_for_period, F.text == "🏠 Bosh sahifa")
async def monitoring_period_home(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@monitoring_router.message(MonitoringStates.waiting_for_period, F.text == "⬅️ Ortga")
async def monitoring_period_back(message: types.Message, state: FSMContext):
    data = await state.get_data()
    role = data.get("selected_role", "Admin")
    await state.set_state(MonitoringStates.waiting_for_employee_choice)
    await message.answer(f"👤 {role}lardan birini tanlang:", reply_markup=get_employee_list_keyboard(role))


@monitoring_router.message(MonitoringStates.waiting_for_period, F.text == "📅 Bugun")
async def monitoring_period_today(message: types.Message, state: FSMContext):
    data = await state.get_data()
    uid = data.get("selected_user_id")
    name = data.get("selected_name")
    today = datetime.now(TASHKENT_TZ).strftime("%Y-%m-%d")

    if uid == "ALL":
        await send_all_employees_report(message, today, today, f"📅 Bugungi ({today}) hisobot")
    else:
        records = await get_attendance_by_user_today(uid)
        report = await format_attendance_report(records, f"📅 <b>{name} — Bugungi ({today}) hisobot</b>")
        await message.answer(report, parse_mode="HTML", reply_markup=get_period_keyboard())


@monitoring_router.message(MonitoringStates.waiting_for_period, F.text == "📅 Bu oy")
async def monitoring_period_this_month(message: types.Message, state: FSMContext):
    data = await state.get_data()
    uid = data.get("selected_user_id")
    name = data.get("selected_name")
    now = datetime.now(TASHKENT_TZ)

    if uid == "ALL":
        dates = get_all_days_in_current_month()
        await send_all_employees_report(message, dates[0], dates[-1], f"📅 {now.year}-{now.month:02d} oylik hisobot")
    else:
        records = await get_attendance_by_user_and_month(uid, now.year, now.month)
        title = f"📅 <b>{name} — {now.year}-{now.month:02d} oylik hisobot</b>"
        report = await format_attendance_report(records, title)
        await message.answer(report, parse_mode="HTML", reply_markup=get_period_keyboard())


@monitoring_router.message(MonitoringStates.waiting_for_period, F.text == "📆 Sana (multiple select)")
async def monitoring_period_custom(message: types.Message, state: FSMContext):
    await state.set_state(MonitoringStates.waiting_for_custom_dates)
    await message.answer(
        text=(
            "📆 <b>Sanalarni kiriting</b>\n\n"
            "Bir yoki bir nechta sanani vergul bilan ajratib yozing:\n"
            "Masalan: <code>2026-05-01, 2026-05-05, 2026-05-10</code>"
        ),
        parse_mode="HTML",
        reply_markup=get_back_home_keyboard()
    )


@monitoring_router.message(MonitoringStates.waiting_for_period)
async def invalid_period_selected(message: types.Message):
    await message.answer("❌ Iltimos, tugmalardan birini tanlang!", reply_markup=get_period_keyboard())


# ================= CUSTOM SANALAR =================
@monitoring_router.message(MonitoringStates.waiting_for_custom_dates, F.text == "🏠 Bosh sahifa")
async def monitoring_custom_dates_home(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@monitoring_router.message(MonitoringStates.waiting_for_custom_dates, F.text == "⬅️ Ortga")
async def monitoring_custom_dates_back(message: types.Message, state: FSMContext):
    await state.set_state(MonitoringStates.waiting_for_period)
    await message.answer("Davr tanlang:", reply_markup=get_period_keyboard())


@monitoring_router.message(MonitoringStates.waiting_for_custom_dates)
async def monitoring_custom_dates_entered(message: types.Message, state: FSMContext):
    import re
    raw = message.text.strip()
    dates = [d.strip() for d in raw.split(",") if re.match(r"\d{4}-\d{2}-\d{2}", d.strip())]

    if not dates:
        await message.answer(
            "❌ Noto'g'ri format. Masalan: <code>2026-05-01, 2026-05-05</code>",
            parse_mode="HTML"
        )
        return

    data = await state.get_data()
    uid = data.get("selected_user_id")
    name = data.get("selected_name")
    dates_str = ", ".join(dates)

    if uid == "ALL":
        await send_all_employees_report(message, dates[0], dates[-1], f"📆 Tanlangan sanalar: {dates_str}")
    else:
        records = await get_attendance_by_dates(uid, dates)
        title = f"📆 <b>{name} — {dates_str}</b>"
        report = await format_attendance_report(records, title)
        await message.answer(report, parse_mode="HTML", reply_markup=get_period_keyboard())

    await state.set_state(MonitoringStates.waiting_for_period)


# ================= BARCHA XODIMLAR UCHUN HISOBOT =================
async def send_all_employees_report(message: types.Message, start_date: str, end_date: str, title: str):
    state = await message.bot.get_state(message.from_user.id)
    state_data = {}
    if state and state.data:
        state_data = state.data
    
    role = state_data.get("selected_role", "Admin")
    employees = get_all_users_by_role(role)
    
    if not employees:
        await message.answer("📭 Xodimlar topilmadi.", reply_markup=get_period_keyboard())
        return

    full_text = f"👥 <b>{title}</b>\n\n"
    
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    date_list = []
    current = start
    while current <= end:
        date_list.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    
    # Bayram kunlarini olish
    holidays_set = await get_holiday_dates()
    
    for uid, name in employees:
        records = await get_attendance_by_dates(uid, date_list)
        
        # Faqat bayram bo'lmagan kunlardagi kech qolishlarni hisoblash
        total_min = 0
        for r in records:
            r_date = r.get("date", "")
            if is_holiday_date(r_date, holidays_set):
                continue
            total_min += r.get("late_minutes", 0)
        
        h, m = divmod(total_min, 60)
        full_text += f"👤 <b>{name}</b>\n   📌 Kech qolishlar: {len([r for r in records if not is_holiday_date(r.get('date'), holidays_set)])} ta\n   ⏱ Jami: {h} soat {m} daqiqa\n\n"

    await message.answer(full_text, parse_mode="HTML", reply_markup=get_period_keyboard())


# ================= KECH QOLISH =================
@monitoring_router.message(MonitoringStates.waiting_for_role, F.text == "⏰ Kech qolish")
@monitoring_router.message(F.text == "⏰ Kech qoldim")
async def late_start_handler(message: types.Message, state: FSMContext):
    await state.set_state(MonitoringStates.waiting_for_late_time)
    await message.answer(
        text=(
            "⏰ <b>Kech qolish vaqtini kiriting</b>\n\n"
            "Hozirgi kelgan vaqtingizni yozing:\n"
            "Masalan: <code>09:25</code>"
        ),
        parse_mode="HTML",
        reply_markup=get_back_home_keyboard()
    )


@monitoring_router.message(MonitoringStates.waiting_for_late_time, F.text == "🏠 Bosh sahifa")
async def late_time_home(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@monitoring_router.message(MonitoringStates.waiting_for_late_time, F.text == "⬅️ Ortga")
async def late_time_back(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@monitoring_router.message(MonitoringStates.waiting_for_late_time)
async def late_time_entered(message: types.Message, state: FSMContext):
    import re
    time_text = message.text.strip()
    if not re.match(r"^([0-1]?\d|2[0-3]):[0-5]\d$", time_text):
        await message.answer("❌ Noto'g'ri format. Masalan: <code>09:25</code>", parse_mode="HTML")
        return

    now = datetime.now(TASHKENT_TZ)
    user_id = str(message.from_user.id)
    
    work_start, work_end = await get_user_work_time(user_id)

    try:
        ws_h, ws_m = map(int, work_start.split(":"))
        ar_h, ar_m = map(int, time_text.split(":"))
        late_min = (ar_h * 60 + ar_m) - (ws_h * 60 + ws_m)
        late_min = max(0, late_min)
    except Exception:
        late_min = 0

    await state.update_data(
        arrived_at=time_text,
        late_minutes=late_min,
        late_date=now.strftime("%Y-%m-%d")
    )
    await state.set_state(MonitoringStates.waiting_for_late_reason)
    await message.answer(
        text=(
            f"⏰ Kelgan vaqt: <b>{time_text}</b> | "
            f"Ish boshlanish: <b>{work_start}</b> | "
            f"Kechikish: <b>{late_min} daqiqa</b>\n\n"
            "✍️ <b>Kech qolish sababini kiriting:</b>"
        ),
        parse_mode="HTML",
        reply_markup=get_back_home_keyboard()
    )


@monitoring_router.message(MonitoringStates.waiting_for_late_reason, F.text == "🏠 Bosh sahifa")
async def late_reason_home(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@monitoring_router.message(MonitoringStates.waiting_for_late_reason, F.text == "⬅️ Ortga")
async def late_reason_back(message: types.Message, state: FSMContext):
    await state.set_state(MonitoringStates.waiting_for_late_time)
    await message.answer(
        "Kelgan vaqtingizni qayta kiriting (masalan: <code>09:25</code>):",
        parse_mode="HTML",
        reply_markup=get_back_home_keyboard()
    )


@monitoring_router.message(MonitoringStates.waiting_for_late_reason)
async def late_reason_entered(message: types.Message, state: FSMContext):
    data = await state.get_data()
    attendance_id = data.get("pending_attendance_id")
    reason = message.text.strip()
    user_name = data.get("user_name")
    role = data.get("role")
    arrived_at = data.get("arrived_at")
    today = data.get("today")
    late_minutes = data.get("late_minutes")
    
    from utils.attendance_db import update_attendance_reason
    await update_attendance_reason(attendance_id, reason)
    
    await state.clear()
    await message.answer(
        text=(
            f"✅ <b>Kech qolish sababi qabul qilindi!</b>\n\n"
            f"📅 Sana: {today}\n"
            f"⏰ Kelgan vaqt: {arrived_at}\n"
            f"⚠️ Kechikish: {late_minutes} daqiqa\n"
            f"✍️ Sabab: {reason}\n\n"
            f"🌟 <b>E'tiboringiz uchun rahmat, {user_name}!</b>\n"
            f"Kelajakda o'z vaqtida kelishingizni tavsiya qilamiz."
        ),
        parse_mode="HTML",
        reply_markup=get_main_menu(role)
    )


# ============================================================
#  ✅ ISHGA KELDIM — xodim ishga kelganini tasdiqlaydi
# ============================================================
class CheckInStates(StatesGroup):
    waiting_for_video = State()


@monitoring_router.message(F.text == "✅ Ishga keldim")
async def check_in_start_handler(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    today = datetime.now(TASHKENT_TZ).strftime("%Y-%m-%d")
    
    # ===== BUGUN BAYRAM KUNI TEKSHIRISH =====
    is_holiday = await is_today_global_holiday()
    if is_holiday:
        await message.answer(
            text="🎉 <b>Hurmatli xodim, bugun bayram kuni!</b>\n\n"
                 "Siz dam olishingiz mumkin. Ishga kelish shart emas.\n\n"
                 "Bayram muborak bo'lsin! 🎊",
            parse_mode="HTML",
            reply_markup=get_main_menu(USERS_ROLES.get(user_id, {}).get("role", ""))
        )
        return
    
    if await has_checkin_today(user_id):
        await message.answer(
            f"⚠️ Siz bugun ({today}) allaqachon ishga kelganingizni tasdiqlagansiz!",
            reply_markup=get_main_menu(USERS_ROLES.get(user_id, {}).get("role", ""))
        )
        return
    
    await state.set_state(CheckInStates.waiting_for_video)
    await message.answer(
        text="📹 <b>Ishga kelganingizni tasdiqlash uchun dumaloq video yuboring!</b>\n\n"
             "⚠️ Faqat <b>dumaloq video (video message)</b> qabul qilinadi!\n",
        parse_mode="HTML",
        reply_markup=get_back_home_keyboard()
    )


@monitoring_router.message(CheckInStates.waiting_for_video)
async def check_in_video_handler(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    user_info = USERS_ROLES.get(user_id, {})
    user_name = user_info.get("name", message.from_user.full_name)
    role = user_info.get("role", "")
    now = datetime.now(TASHKENT_TZ)
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")
    
    GROUP_CHAT_ID = -5226036627
    
    if not message.video_note:
        await message.answer(
            text="❌ <b>Noto'g'ri format!</b>\n\n"
                 "Iltimos, faqat <b>dumaloq video (video message)</b> yuboring.\n\n"
                 "📹 <b>Qanday yuborish kerak:</b>\n"
                 "1. Mikrofon tugmasini bosing va ushlab turing\n"
                 "2. <b>Video</b> tugmasiga o'ting\n"
                 "3. Yozish tugmasini bosing\n"
                 "4. Yozib bo'lgach, jo'natish tugmasini bosing",
            parse_mode="HTML"
        )
        return
    
    work_start, work_end = await get_user_work_time(user_id)
    
    try:
        ws_h, ws_m = map(int, work_start.split(":"))
        ar_h, ar_m = map(int, current_time.split(":"))
        if ar_h < 5 and ws_h > 20:
            ar_time = (ar_h + 24) * 60 + ar_m
        else:
            ar_time = ar_h * 60 + ar_m
        ws_time = ws_h * 60 + ws_m
        late_min = max(0, ar_time - ws_time)
    except Exception:
        late_min = 0
    
    if late_min > 0:
        record_id = await add_attendance(
            user_id=user_id,
            user_name=user_name,
            role=role,
            date=today,
            arrived_at=current_time,
            late_minutes=late_min,
            reason=None,
            proof_file_id=message.video_note.file_id,
            proof_type="Video message",
            status="checked_in"
        )
        
        if not record_id:
            await message.answer("❌ Saqlashda xatolik yuz berdi. Qayta urinib ko'ring.")
            await state.clear()
            return
        
        try:
            await message.bot.send_video_note(
                chat_id=GROUP_CHAT_ID,
                video_note=message.video_note.file_id
            )
            await message.bot.send_message(
                chat_id=GROUP_CHAT_ID,
                text=f"✅ <b>Xodim ishga keldi!</b>\n\n"
                     f"👤 <b>Xodim:</b> {user_name}\n"
                     f"📅 <b>Sana:</b> {today}\n"
                     f"⏰ <b>Kelgan vaqt:</b> {current_time}\n"
                     f"📋 <b>Ish vaqti:</b> {work_start} - {work_end}\n"
                     f"⚠️ <b>Kechikish:</b> {late_min} daqiqa",
                parse_mode="HTML"
            )
        except Exception as e:
            logging.error(f"Isbotni guruhga yuborishda xatolik: {e}")
        
        await state.update_data(
            pending_attendance_id=record_id,
            user_name=user_name,
            role=role,
            work_start=work_start,
            work_end=work_end,
            arrived_at=current_time,
            today=today,
            late_minutes=late_min
        )
        await state.set_state(MonitoringStates.waiting_for_late_reason)
        await message.answer(
            text=(
                f"⚠️ <b>Hurmatli {user_name}, siz ishga {late_min} daqiqa kech qoldingiz.</b>\n\n"
                f"📅 Sana: {today}\n"
                f"⏰ Kelgan vaqt: {current_time}\n"
                f"📋 Ish vaqti: {work_start} - {work_end}\n\n"
                f"✍️ <b>Iltimos, kech qolish sababini kiriting:</b>"
            ),
            parse_mode="HTML",
            reply_markup=get_back_home_keyboard()
        )
        return
    
    record_id = await add_attendance(
        user_id=user_id,
        user_name=user_name,
        role=role,
        date=today,
        arrived_at=current_time,
        late_minutes=0,
        reason="Ishga kelish tasdiqlandi",
        proof_file_id=message.video_note.file_id,
        proof_type="Video message",
        status="checked_in"
    )
    
    if not record_id:
        await message.answer("❌ Saqlashda xatolik yuz berdi. Qayta urinib ko'ring.")
        await state.clear()
        return
    
    try:
        await message.bot.send_video_note(
            chat_id=GROUP_CHAT_ID,
            video_note=message.video_note.file_id
        )
        await message.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=f"✅ <b>Xodim ishga keldi!</b>\n\n"
                 f"👤 <b>Xodim:</b> {user_name}\n"
                 f"📅 <b>Sana:</b> {today}\n"
                 f"⏰ <b>Kelgan vaqt:</b> {current_time}\n"
                 f"📋 <b>Ish vaqti:</b> {work_start} - {work_end}",
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Isbotni guruhga yuborishda xatolik: {e}")
    
    await state.clear()
    
    try:
        ws_h, ws_m = map(int, work_start.split(":"))
        ar_h, ar_m = map(int, current_time.split(":"))
        ar_time = ar_h * 60 + ar_m
        ws_time = ws_h * 60 + ws_m
        early_min = ws_time - ar_time
        if early_min < 0:
            early_min = 0
    except:
        early_min = 0
    
    if early_min > 0:
        # Navbatdagi motivatsion xabarni olish va indeksni oldinga surish
        mot_index = await get_motivation_index(user_id)
        mot_message = MOTIVATION_MESSAGES[mot_index % len(MOTIVATION_MESSAGES)]
        await increment_motivation_index(user_id, total=len(MOTIVATION_MESSAGES))

        await message.answer(
            text=(
                f"✅ <b>Ishga kelishingiz tasdiqlandi!</b>\n\n"
                f"📅 Sana: {today}\n"
                f"⏰ Kelgan vaqt: {current_time}\n"
                f"📋 Ish vaqti: {work_start} - {work_end}\n"
                f"⏩ <b>Hurmatli {user_name}, siz ishga {early_min} daqiqa oldin keldingiz!</b>\n\n"
                f"{mot_message}\n\n"
                f"📸 Isbot rahbarga yuborildi."
            ),
            parse_mode="HTML",
            reply_markup=get_main_menu(role)
        )
    else:
        await message.answer(
            text=(
                f"✅ <b>Ishga kelishingiz tasdiqlandi!</b>\n\n"
                f"📅 Sana: {today}\n"
                f"⏰ Kelgan vaqt: {current_time}\n"
                f"📋 Ish vaqti: {work_start} - {work_end}\n"
                f"🎉 <b>Hurmatli {user_name}, siz ishga o'z vaqtida keldingiz. Kuningiz barokatli o'tsin!</b>\n"
                f"📸 Isbot rahbarga yuborildi."
            ),
            parse_mode="HTML",
            reply_markup=get_main_menu(role)
        )


@monitoring_router.message(CheckInStates.waiting_for_video, F.text == "🏠 Bosh sahifa")
async def check_in_home(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))


@monitoring_router.message(CheckInStates.waiting_for_video, F.text == "⬅️ Ortga")
async def check_in_back(message: types.Message, state: FSMContext):
    await state.clear()
    role = USERS_ROLES.get(str(message.from_user.id), {}).get("role", "Owner")
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu(role))
