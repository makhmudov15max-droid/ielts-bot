import logging
from datetime import datetime, timedelta, timezone
from utils.database import get_pool

TASHKENT_TZ = timezone(timedelta(hours=5))


async def init_holidays_table():
    """holidays jadvalini yaratish"""
    pool = get_pool()
    if not pool:
        return
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS holidays (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    user_name TEXT,
                    role TEXT,
                    name TEXT NOT NULL,
                    date TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_holidays_user ON holidays(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_holidays_date ON holidays(date)")
            logging.info("✅ holidays jadvali tayyor")
    except Exception as e:
        logging.error(f"init_holidays_table xatosi: {e}")


async def add_holiday(user_id: str, user_name: str, role: str, name: str, date: str):
    """Yangi ta'til qo'shish"""
    pool = get_pool()
    if not pool:
        return None
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO holidays (user_id, user_name, role, name, date)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """, user_id, user_name, role, name, date)
            return row["id"]
    except Exception as e:
        logging.error(f"add_holiday xatosi: {e}")
        return None


async def get_holidays_by_user(user_id: str):
    """Xodimning barcha ta'tillarini olish"""
    pool = get_pool()
    if not pool:
        return []
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, name, date FROM holidays
                WHERE user_id = $1
                ORDER BY date ASC
            """, user_id)
            return [dict(row) for row in rows]
    except Exception as e:
        logging.error(f"get_holidays_by_user xatosi: {e}")
        return []


async def get_holidays_by_role(role: str):
    """Rol bo'yicha barcha ta'tillarni olish"""
    pool = get_pool()
    if not pool:
        return []
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, user_id, user_name, name, date FROM holidays
                WHERE role = $1
                ORDER BY date ASC
            """, role)
            return [dict(row) for row in rows]
    except Exception as e:
        logging.error(f"get_holidays_by_role xatosi: {e}")
        return []


async def update_holiday(holiday_id: int, name: str, date: str):
    """Ta'tilni yangilash"""
    pool = get_pool()
    if not pool:
        return False
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE holidays SET name = $1, date = $2, updated_at = CURRENT_TIMESTAMP
                WHERE id = $3
            """, name, date, holiday_id)
            return True
    except Exception as e:
        logging.error(f"update_holiday xatosi: {e}")
        return False


async def delete_holiday(holiday_id: int):
    """Ta'tilni o'chirish"""
    pool = get_pool()
    if not pool:
        return False
    try:
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM holidays WHERE id = $1", holiday_id)
            return True
    except Exception as e:
        logging.error(f"delete_holiday xatosi: {e}")
        return False


async def delete_all_holidays_by_user(user_id: str):
    """Xodimning barcha ta'tillarini o'chirish"""
    pool = get_pool()
    if not pool:
        return False
    try:
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM holidays WHERE user_id = $1", user_id)
            return True
    except Exception as e:
        logging.error(f"delete_all_holidays_by_user xatosi: {e}")
        return False
