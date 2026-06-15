"""
ORBIT HQ — Dizayn tizimi (Design System)

Barcha xabarlar uchun yagona format standarti.
Har bir xabar turi uchun prefiks emoji va HTML shabloni.
"""

# ================= EMOJI STANDARTI =================

# Muvaffaqiyat
SUCCESS = "✅"

# Xatolik
ERROR = "❌"

# Ogohlantirish
WARNING = "⚠️"

# Ma'lumot / info
INFO = "ℹ️"

# Yuklanmoqda / loading
LOADING = "⏳"

# Bo'sh holat
EMPTY = "📭"

# Sarlavha
TITLE = "📌"

# Savol
QUESTION = "❓"

# Tasdiqlash
CONFIRM = "🔐"

# Navigatsiya
BACK = "⬅️"
HOME = "🏠"

# Ishga kelish
CHECK_IN = "✅"

# Vazifalar
TASK = "📋"

# Monitoring
MONITORING = "🎯"

# Hisobot
REPORT = "📊"

# Sozlamalar
SETTINGS = "⚙️"

# Xodimlar
STAFF = "👥"

# Arxiv
ARCHIVE = "🗄"

# Moliya
FINANCE = "💰"

# Bayram
HOLIDAY = "🌴"

# Ish vaqti
WORKTIME = "🏢"


# ================= XABAR SHABLONLARI =================

def success(text: str) -> str:
    """Muvaffaqiyatli amal xabari"""
    return f"{SUCCESS} <b>{text}</b>"

def error(text: str) -> str:
    """Xatolik xabari"""
    return f"{ERROR} {text}"

def warning(text: str) -> str:
    """Ogohlantirish xabari"""
    return f"{WARNING} <b>{text}</b>"

def info(text: str) -> str:
    """Ma'lumot xabari"""
    return f"{INFO} {text}"

def empty_state(text: str, action_hint: str = "") -> str:
    """Bo'sh holat xabari"""
    msg = f"{EMPTY} {text}"
    if action_hint:
        msg += f"\n\n{INFO} {action_hint}"
    return msg

def breadcrumb(steps: list) -> str:
    """Navigatsiya izi: ['Monitoring', 'Admin', 'Xodim']"""
    return f"📍 {' › '.join(steps)}"

def progress_bar(current: int, total: int, width: int = 20) -> str:
    """Matnli progress bar: ████████░░░░░░░░░░░░ 40%"""
    if total == 0:
        return "░" * width + " 0%"
    percent = min(100, int(current / total * 100))
    filled = int(width * current / total)
    bar = "█" * filled + "░" * (width - filled)
    return f"{bar} {percent}%"

def confirm_dialog(title: str, description: str, yes_text: str = "✅ Ha, davom etish", no_text: str = "❌ Yo'q, bekor qilish") -> str:
    """Tasdiqlash dialogi"""
    return f"{CONFIRM} <b>{title}</b>\n\n{description}"

def step_progress(current: int, total: int, step_name: str) -> str:
    """Ko'p qadamli jarayon uchun progress ko'rsatkichi"""
    bar = "━" * current + "┈" * (total - current)
    return f"<b>{step_name}</b>\n{bar} ({current}/{total})"
