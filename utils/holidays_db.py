import logging
import re
from datetime import datetime, timedelta, timezone
from utils.database import get_pool

TASHKENT_TZ = timezone(timedelta(hours=5))


async def add_holiday(user_id: str, user_name: str, role: str, name: str, date: str, is_repeat: bool = False):
    """Yangi ta'til qo'shish"""
    pool = get_pool()
    if not pool:
        logging.error("add_holiday: pool mavjud emas")
        return None
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO holidays (user_id, user_name, role, name, date, is_repeat)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """, user_id, user_name, role, name, date, is_repeat)
            logging.info(f"add_holiday: ID={row['id']} qo'shildi (user={user_id}, name={name})")
            return row["id"]
    except Exception as e:
        logging.error(f"add_holiday xatosi: {e}")
        return None


async def add_holiday_for_all(name: str, date: str, is_repeat: bool = False):
    """Barcha xodimlar uchun ta'til qo'shish"""
    from utils.users_db import load_users
    
    users = await load_users()
    if not users:
        logging.error("add_holiday_for_all: users yuklanmadi!")
        return 0
    
    count = 0
    for user_id, user_info in users.items():
        if isinstance(user_info, dict):
            user_name = user_info.get("name", "")
            user_role = user_info.get("role", "")
        else:
            user_name = ""
            user_role = str(user_info) if user_info else ""
        
        result = await add_holiday(
            str(user_id),
            user_name,
            user_role,
            name,
            date,
            is_repeat
        )
        if result:
            count += 1
    
    logging.info(f"add_holiday_for_all: {count} ta xodimga ta'til qo'shildi")
    return count


async def get_all_holidays():
    """Barcha ta'tillarni olish (unique)"""
    pool = get_pool()
    if not pool:
        return []
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT DISTINCT ON (name, date) id, name, date, is_repeat
                FROM holidays
                ORDER BY name, date, id DESC
            """)
            return [dict(row) for row in rows]
    except Exception as e:
        logging.error(f"get_all_holidays xatosi: {e}")
        return []


async def get_holiday_by_id(holiday_id: int):
    """ID bo'yicha ta'til olish"""
    pool = get_pool()
    if not pool:
        return None
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM holidays WHERE id = $1", holiday_id)
            return dict(row) if row else None
    except Exception as e:
        logging.error(f"get_holiday_by_id xatosi: {e}")
        return None


async def update_holiday(holiday_id: int, name: str = None, date: str = None):
    """Ta'tilni yangilash (barcha xodimlar uchun)"""
    pool = get_pool()
    if not pool:
        return False
    
    try:
        async with pool.acquire() as conn:
            old = await get_holiday_by_id(holiday_id)
            if not old:
                return False
            
            new_name = name if name else old["name"]
            new_date = date if date else old["date"]
            
            is_repeat = bool(re.match(r"^\d{2}-\d{2}$", new_date))
            
            await conn.execute("""
                UPDATE holidays 
                SET name = $1, date = $2, is_repeat = $3, updated_at = CURRENT_TIMESTAMP
                WHERE name = $4 AND date = $5
            """, new_name, new_date, is_repeat, old["name"], old["date"])
            
            logging.info(f"update_holiday: {old['name']} -> {new_name} updated")
            return True
    except Exception as e:
        logging.error(f"update_holiday xatosi: {e}")
        return False


async def delete_holiday(holiday_id: int):
    """Ta'tilni o'chirish (barcha xodimlar uchun)"""
    pool = get_pool()
    if not pool:
        return False
    
    try:
        async with pool.acquire() as conn:
            holiday = await get_holiday_by_id(holiday_id)
            if not holiday:
                return False
            
            await conn.execute("""
                DELETE FROM holidays WHERE name = $1 AND date = $2
            """, holiday["name"], holiday["date"])
            
            logging.info(f"delete_holiday: {holiday['name']} deleted")
            return True
    except Exception as e:
        logging.error(f"delete_holiday xatosi: {e}")
        return False


async def is_today_holiday(user_id: str) -> bool:
    """Bugun foydalanuvchi uchun ta'til kunimi tekshirish"""
    today = datetime.now(TASHKENT_TZ)
    today_full = today.strftime("%Y-%m-%d")
    today_repeat = today.strftime("%m-%d")
    
    pool = get_pool()
    if not pool:
        return False
    
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id FROM holidays 
                WHERE user_id = $1 AND (date = $2 OR (is_repeat = TRUE AND date = $3))
                LIMIT 1
            """, user_id, today_full, today_repeat)
            return row is not None
    except Exception as e:
        logging.error(f"is_today_holiday xatosi: {e}")
        return False
