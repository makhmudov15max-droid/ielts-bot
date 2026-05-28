import logging
import re
from datetime import datetime, timedelta, timezone
from utils.database import get_pool

TASHKENT_TZ = timezone(timedelta(hours=5))


async def add_holidays_bulk(holidays: list) -> tuple:
    """
    Bir nechta global ta'tilni bir vaqtda saqlaydi.
    holidays: [(name, db_date, is_repeat), ...]
    Qaytaradi: (saved_count, skipped_count)
    """
    pool = get_pool()
    if not pool:
        logging.error("add_holidays_bulk: pool mavjud emas")
        return 0, 0

    saved = 0
    skipped = 0

    try:
        async with pool.acquire() as conn:
            for name, date, is_repeat in holidays:
                existing = await conn.fetchrow(
                    "SELECT id FROM holidays WHERE name = $1 AND date = $2 AND user_id = 'global'",
                    name, date
                )
                if existing:
                    skipped += 1
                    logging.info(f"add_holidays_bulk: '{name}' ({date}) allaqachon mavjud — o'tkazib yuborildi")
                    continue

                row = await conn.fetchrow("""
                    INSERT INTO holidays (user_id, user_name, role, name, date, is_repeat)
                    VALUES ('global', 'Global', 'all', $1, $2, $3)
                    RETURNING id
                """, name, date, is_repeat)

                if row:
                    saved += 1
                    logging.info(f"add_holidays_bulk: '{name}' ({date}) saqlandi, ID={row['id']}")
                else:
                    logging.error(f"add_holidays_bulk: '{name}' ({date}) saqlanmadi")

    except Exception as e:
        logging.error(f"add_holidays_bulk xatosi: {e}")

    logging.info(f"add_holidays_bulk: {saved} saqlandi, {skipped} o'tkazib yuborildi")
    return saved, skipped



async def delete_all_holidays():
    """Barcha global ta'tillarni o'chirish"""
    pool = get_pool()
    if not pool:
        return 0
    try:
        async with pool.acquire() as conn:
            result = await conn.execute("DELETE FROM holidays WHERE user_id = 'global'")
            # "DELETE N" formatidan N ni olish
            count = int(result.split()[-1]) if result else 0
            logging.info(f"delete_all_holidays: {count} ta ta'til o'chirildi")
            return count
    except Exception as e:
        logging.error(f"delete_all_holidays xatosi: {e}")
        return 0

# Eski nom — orqaga moslik uchun (boshqa joyda ishlatilsa)
async def add_holiday_for_all(name: str, date: str, is_repeat: bool = False):
    saved, _ = await add_holidays_bulk([(name, date, is_repeat)])
    return saved


async def get_all_holidays():
    """Barcha global ta'tillarni olish, sanasi bo'yicha tartiblanadi"""
    pool = get_pool()
    if not pool:
        return []
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT DISTINCT ON (name, date) id, name, date, is_repeat
                FROM holidays
                WHERE user_id = 'global'
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
    """Ta'tilni yangilash"""
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

            # is_repeat: MM-DD formatida bo'lsa True
            is_repeat = bool(re.match(r"^\d{2}-\d{2}$", new_date))

            await conn.execute("""
                UPDATE holidays
                SET name = $1, date = $2, is_repeat = $3, updated_at = CURRENT_TIMESTAMP
                WHERE id = $4
            """, new_name, new_date, is_repeat, holiday_id)

            logging.info(f"update_holiday: ID={holiday_id} '{old['name']}' -> '{new_name}' yangilandi")
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
            holiday = await get_holiday_by_id(holiday_id)
            if not holiday:
                return False

            await conn.execute("DELETE FROM holidays WHERE id = $1", holiday_id)
            logging.info(f"delete_holiday: ID={holiday_id} '{holiday['name']}' o'chirildi")
            return True
    except Exception as e:
        logging.error(f"delete_holiday xatosi: {e}")
        return False


async def is_today_holiday(user_id: str) -> bool:
    """Bugun ta'til kunimi tekshirish (global ta'tillar)"""
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
                WHERE user_id = 'global'
                  AND (date = $1 OR (is_repeat = TRUE AND date = $2))
                LIMIT 1
            """, today_full, today_repeat)
            return row is not None
    except Exception as e:
        logging.error(f"is_today_holiday xatosi: {e}")
        return False

# utils/holidays_db.py ga qo'shing:

async def is_today_global_holiday() -> bool:
    """Bugun global ta'til kunimi tekshirish (har qanday xodim uchun)"""
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
                WHERE user_id = 'global'
                  AND (date = $1 OR (is_repeat = TRUE AND date = $2))
                LIMIT 1
            """, today_full, today_repeat)
            return row is not None
    except Exception as e:
        logging.error(f"is_today_global_holiday xatosi: {e}")
        return False
