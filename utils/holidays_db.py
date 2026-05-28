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

async def get_holiday_by_id(holiday_id: int):
    """ID bo'yicha ta'tilni olish"""
    pool = get_pool()
    if not pool:
        return None
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, user_id, user_name, role, name, date FROM holidays
                WHERE id = $1
            """, holiday_id)
            if row:
                return dict(row)
            return None
    except Exception as e:
        logging.error(f"get_holiday_by_id xatosi: {e}")
        return None

async def add_holiday_for_all(name: str, date: str):
    """Barcha xodimlar uchun ta'til qo'shish"""
    from utils.users_db import load_users
    
    users = await load_users()
    count = 0
    for user_id, user_info in users.items():
        # Owner, Manager, Admin, Kassir, Sanitar larning barchasiga qo'shamiz
        result = await add_holiday(user_id, user_info.get("name", ""), user_info.get("role", ""), name, date)
        if result:
            count += 1
    return count


async def get_all_holidays():
    """Barcha ta'tillarni olish (unique)"""
    pool = get_pool()
    if not pool:
        return []
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT DISTINCT id, name, date FROM holidays
                ORDER BY date ASC
            """)
            # Duplicate larni olib tashlash (name va date bo'yicha)
            unique = {}
            for row in rows:
                key = f"{row['name']}_{row['date']}"
                if key not in unique:
                    unique[key] = dict(row)
            return list(unique.values())
    except Exception as e:
        logging.error(f"get_all_holidays xatosi: {e}")
        return []
