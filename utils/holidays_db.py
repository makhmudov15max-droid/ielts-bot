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


async def add_holiday(user_id: str, user_name: str, role: str, name: str, date: str, is_repeat: bool = False):
    """Yangi ta'til qo'shish (is_repeat = True bo'lsa, har yili takrorlanadi)"""
    pool = get_pool()
    if not pool:
        return None
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO holidays (user_id, user_name, role, name, date, is_repeat)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """, user_id, user_name, role, name, date, is_repeat)
            return row["id"]
    except Exception as e:
        logging.error(f"add_holiday xatosi: {e}")
        return None


async def add_holiday_for_all(name: str, date: str, is_repeat: bool = False):
    """Barcha xodimlar uchun ta'til qo'shish"""
    from utils.users_db import load_users
    
    users = await load_users()
    count = 0
    for user_id, user_info in users.items():
        # Owner, Manager, Admin, Kassir, Sanitar larning barchasiga qo'shamiz
        result = await add_holiday(user_id, user_info.get("name", ""), user_info.get("role", ""), name, date, is_repeat)
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
