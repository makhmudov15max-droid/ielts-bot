import logging
from datetime import datetime, timedelta, timezone
from utils.database import get_pool

TASHKENT_TZ = timezone(timedelta(hours=5))


# ================= TARIFLAR (fines_tariffs) =================

async def init_fines_tables():
    """Jadvallarni yaratish (database.py da ham bor, xavfsizlik uchun)"""
    pool = get_pool()
    if not pool:
        return
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS fines_tariffs (
                    id SERIAL PRIMARY KEY,
                    role TEXT NOT NULL,
                    min_minutes INTEGER NOT NULL,
                    max_minutes INTEGER NOT NULL,
                    amount INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS fines (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    user_name TEXT,
                    role TEXT,
                    date TEXT NOT NULL,
                    late_minutes INTEGER DEFAULT 0,
                    amount INTEGER DEFAULT 0,
                    reason TEXT DEFAULT 'late',
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    cancelled_at TIMESTAMP
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_fines_tariffs_role ON fines_tariffs(role)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_fines_user ON fines(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_fines_date ON fines(date)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_fines_status ON fines(status)")
    except Exception as e:
        logging.error(f"init_fines_tables xatosi: {e}", exc_info=True)


async def get_tariffs_for_role(role: str) -> list:
    """Berilgan rol uchun barcha tariflar (daqiqa bo'yicha saralangan)"""
    pool = get_pool()
    if not pool:
        return []
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM fines_tariffs WHERE role = $1 ORDER BY min_minutes ASC
            """, role)
            return [dict(r) for r in rows]
    except Exception as e:
        logging.error(f"get_tariffs_for_role xatosi: {e}", exc_info=True)
        return []


async def find_tariff_for_minutes(role: str, late_minutes: int):
    """Kechikish daqiqasiga mos tarif summasini topish (interval ichida)"""
    tariffs = await get_tariffs_for_role(role)
    for t in tariffs:
        if t["min_minutes"] <= late_minutes <= t["max_minutes"]:
            return t
    return None


async def save_tariffs_for_role(role: str, tariffs: list):
    """Rol uchun barcha tariflarni saqlash (eski tariflarni o'chirib yangilarini yozadi)
    tariffs: [(min_minutes, max_minutes, amount), ...]
    """
    pool = get_pool()
    if not pool:
        return False
    try:
        async with pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("DELETE FROM fines_tariffs WHERE role = $1", role)
                for min_m, max_m, amount in tariffs:
                    await conn.execute("""
                        INSERT INTO fines_tariffs (role, min_minutes, max_minutes, amount)
                        VALUES ($1, $2, $3, $4)
                    """, role, min_m, max_m, amount)
        return True
    except Exception as e:
        logging.error(f"save_tariffs_for_role xatosi: {e}", exc_info=True)
        return False


async def clear_tariffs_for_role(role: str):
    """Rol uchun barcha tariflarni o'chirish"""
    pool = get_pool()
    if not pool:
        return False
    try:
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM fines_tariffs WHERE role = $1", role)
        return True
    except Exception as e:
        logging.error(f"clear_tariffs_for_role xatosi: {e}", exc_info=True)
        return False


# ================= JARIMALAR (fines) =================

async def add_fine(user_id: str, user_name: str, role: str, date: str,
                   late_minutes: int, amount: int, reason: str = "late") -> int:
    """Yangi jarima qo'shish. status='active'. id qaytaradi."""
    pool = get_pool()
    if not pool:
        return 0
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO fines (user_id, user_name, role, date, late_minutes, amount, reason, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7, 'active')
                RETURNING id
            """, user_id, user_name, role, date, late_minutes, amount, reason)
            return row["id"]
    except Exception as e:
        logging.error(f"add_fine xatosi: {e}", exc_info=True)
        return 0


async def cancel_fine(fine_id: int, new_amount: int = None):
    """Jarimani bekor qilish (status='cancelled') yoki summasi o'zgarishi"""
    pool = get_pool()
    if not pool:
        return False
    try:
        async with pool.acquire() as conn:
            if new_amount is not None:
                # Qisqartirish: summa o'zgaradi, status active qoladi
                await conn.execute("""
                    UPDATE fines SET amount = $1 WHERE id = $2
                """, new_amount, fine_id)
            else:
                # Bekor qilish
                await conn.execute("""
                    UPDATE fines SET status = 'cancelled', cancelled_at = NOW() WHERE id = $1
                """, fine_id)
        return True
    except Exception as e:
        logging.error(f"cancel_fine xatosi: {e}", exc_info=True)
        return False


async def get_user_fines_for_month(user_id: str, year: int, month: int) -> list:
    """Xodimning bir oydagi barcha jarimalari"""
    pool = get_pool()
    if not pool:
        return []
    try:
        month_str = f"{year}-{month:02d}"
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM fines WHERE user_id = $1 AND date LIKE $2
                ORDER BY date ASC, created_at ASC
            """, user_id, f"{month_str}%")
            return [dict(r) for r in rows]
    except Exception as e:
        logging.error(f"get_user_fines_for_month xatosi: {e}", exc_info=True)
        return []


async def get_user_active_fines_total(user_id: str, year: int, month: int) -> int:
    """Xodimning bir oydagi faol (bekor qilinmagan) jarimalari yig'indisi"""
    fines = await get_user_fines_for_month(user_id, year, month)
    return sum(f["amount"] for f in fines if f["status"] == "active")


async def has_active_fine_in_month(user_id: str, year: int, month: int) -> bool:
    """Xodimda oyda faol jarima bormi (bonus shartini tekshirish)"""
    fines = await get_user_fines_for_month(user_id, year, month)
    return any(f["status"] == "active" for f in fines)


async def get_fine_by_id(fine_id: int):
    pool = get_pool()
    if not pool:
        return None
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM fines WHERE id = $1", fine_id)
            return dict(row) if row else None
    except Exception as e:
        logging.error(f"get_fine_by_id xatosi: {e}", exc_info=True)
        return None


async def get_all_active_fines_in_month(year: int, month: int) -> list:
    """Bir oydagi barcha faol jarimalar (owner statistikasi uchun)"""
    pool = get_pool()
    if not pool:
        return []
    try:
        month_str = f"{year}-{month:02d}"
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM fines WHERE date LIKE $1 ORDER BY date ASC
            """, f"{month_str}%")
            return [dict(r) for r in rows]
    except Exception as e:
        logging.error(f"get_all_active_fines_in_month xatosi: {e}", exc_info=True)
        return []
